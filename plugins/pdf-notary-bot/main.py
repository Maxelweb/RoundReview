import os, json, io, hashlib
import base64
import requests
from types import SimpleNamespace
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from pyhanko.sign import SimpleSigner, PdfSignatureMetadata, fields, signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils import images, layout
from pyhanko import stamp
from waitress import serve
from config import (
    log,
    DEBUG,
    API_BASE_URL, 
    API_KEY,
    PLUGIN_CERT_PATH, 
    PLUGIN_KEY_PATH,
    PLUGIN_KEY_PASSPHRASE,
    PLUGIN_NAME,
    PLUGIN_VERSION,
    PLUGIN_BASE_URL,
    PLUGIN_SIGNED_PDFS_FOLDER,
    PLUGIN_SIGN_IMAGE_PATH,
)

# Core definitions
scheduler = BackgroundScheduler()
app = Flask(__name__)
scheduler.start()

# Background service to clean deleted reviews
@scheduler.scheduled_job('interval', hours=24)
def clean_deleted_reviews() -> None:
    log.info("Starting cleaning background service")
    res = requests.get(
        url=f"{API_BASE_URL}/integrations/reviews", 
        headers={"x-api-key": API_KEY}
    )
    if res.status_code != 200:
        log.error("Unable to get reviews for this user")

    # Track all valid object IDs from reviews
    valid_object_ids = set()
    for review in json.loads(res.content).get("reviews", []):
        if review.get("name") != PLUGIN_NAME:
            continue
        object_id = review.get("object_id", None)
        if object_id:
            valid_object_ids.add(object_id)

    # Clean up existing files that don't have reviews
    for file_name in os.listdir(PLUGIN_SIGNED_PDFS_FOLDER):
        if not file_name.endswith('.pdf'):
            continue
        current_object_id = file_name.replace('.pdf', '')
        if current_object_id not in valid_object_ids:
            file_path = os.path.join(PLUGIN_SIGNED_PDFS_FOLDER, file_name)
            log.info("Deleting signed PDF for Object ID = %s", current_object_id)
            os.remove(file_path)
    log.info("Cleaning background service completed")


@app.route('/', methods=['GET'])
def handle_index():
    """ Handle Index """
    return {"plugin_name": PLUGIN_NAME, "plugin_version": PLUGIN_VERSION}, 200

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """ Handle Webhook call """
    data = request.get_json()
    if not data or data.get("event") != "object.updated":
        log.warning("Invalid payload call")
        return {"error": "Invalid payload"}, 400

    object_id, project_id = data.get("object_id"), data.get("project_id")
    status = data.get("updated_fields", {}).get("status")

    if status != "Approved":
        log.info("Notification ignored")
        return {"message": "Notification ignored"}, 200

    res = requests.get(
        url=f"{API_BASE_URL}/objects/{object_id}?raw=1", 
        headers={"x-api-key": API_KEY}
    )

    if res.status_code != 200:
        log.error("Failed to fetch PDF")
        return {"error": "Failed to fetch PDF"}, 500

    object = json.loads(json.dumps(res.json()), object_hook=lambda d: SimpleNamespace(**d)).object
    
    if "NO_SIGNATURE" in object.description: 
        if status != "Approved":
            log.warning("Notification valid, but NO_SIGNATURE found in description. Aborted.")
            return {"message": "Notification valid, but NO_SIGNATURE found in description. Aborted."}, 200
    
    # Sign the PDF
    pdf_writer = IncrementalPdfFileWriter(
        io.BytesIO(
            base64.urlsafe_b64decode(object.raw)
        ), 
        strict=False
    )
    sign_img = None
    if PLUGIN_SIGN_IMAGE_PATH and os.path.exists(PLUGIN_SIGN_IMAGE_PATH):
        log.info("Using signature image at %s", PLUGIN_SIGN_IMAGE_PATH)
        sign_img = images.PdfImage(PLUGIN_SIGN_IMAGE_PATH)
    fields.append_signature_field(pdf_writer, sig_field_spec=fields.SigFieldSpec('Signature1', box=(220,50,15,15)))
    pdf_meta = PdfSignatureMetadata(field_name='Signature1', app_build_props=signers.pdf_byterange.BuildProps(name=PLUGIN_NAME, revision=PLUGIN_VERSION))
    pdf_signer = signers.PdfSigner(
        signature_meta=pdf_meta,
        signer=SimpleSigner.load(
            key_file=PLUGIN_KEY_PATH,
            cert_file=PLUGIN_CERT_PATH,
            key_passphrase=PLUGIN_KEY_PASSPHRASE,
        ),
        stamp_style=stamp.TextStampStyle(
            background=sign_img,
            background_layout=layout.SimpleBoxLayoutRule(x_align=layout.AxisAlignment(3), y_align=layout.AxisAlignment(3)),
            inner_content_layout=layout.SimpleBoxLayoutRule(x_align=layout.AxisAlignment(1), y_align=layout.AxisAlignment(1)),
            stamp_text="Digitally signed by %(signer)s\nTime: %(ts)s\n\nNOTE: the certificate is self-signed;\nverify it with the signer " + f"({object_id[-12:]}).",
        ),
    )
    signed_pdf = pdf_signer.sign_pdf(pdf_writer)

    output_path = f"{PLUGIN_SIGNED_PDFS_FOLDER}/{object_id}.pdf"
    with open(output_path, "wb") as f:
        f.write(signed_pdf.getbuffer())

    log.info("Saved PDF for Object ID = %s and Project ID = %s", object_id, project_id)

    # Prepare unique URL
    pdf_md5 = hashlib.md5(signed_pdf.getbuffer()).hexdigest()[:8]
    encoded_object = base64.urlsafe_b64encode(bytes(object_id + "_" + pdf_md5, "utf-8")).decode("utf-8")

    # Add review for document
    res = requests.post(
        url=f"{API_BASE_URL}/projects/{project_id}/objects/{object_id}/integrations/reviews",
        json={
            "name": PLUGIN_NAME,
            "value": "Your PDF has been **approved**. You can now download the signed version of this document.",
            "icon": "download",
            "url": f"{PLUGIN_BASE_URL}/download/{encoded_object}",
            "url_text": "Download Signed Document",
        },
        headers={"x-api-key": API_KEY}
    )

    if res.status_code != 201:
        log.error("PDF signed and saved, but error occurred while posting new review: %e", res.content)
        return {"error": "PDF signed and saved, but error occurred while posting new review"}, 500
    
    return {"message": "PDF signed and saved and review created", "path": output_path}, 200


@app.route('/download/<base64_code>', methods=['GET'])
def handle_download(base64_code:str):
    """ Handle Download of the stored signed pdf file """
    try:
        base64_id = base64.urlsafe_b64decode(base64_code).decode("utf-8")
    except Exception as e:
        log.error("Error decoding base64 object ID: %s", e)
        return {"error": "Invalid ID"}, 400
    
    if "_" not in base64_id:
        return {"error": "Invalid ID"}, 400
    
    base64_split = base64_id.split("_", maxsplit=2)
    object_id, partial_md5 = base64_split[0], base64_split[1]

    file_path = f"{PLUGIN_SIGNED_PDFS_FOLDER}/{object_id}.pdf"
    if not os.path.exists(file_path):
        return {"error": "ID not found"}, 404

    res = requests.get(
        url=f"{API_BASE_URL}/objects/{object_id}", 
        headers={"x-api-key": API_KEY}
    )

    if res.status_code != 200:
        return {"error": "Failed to fetch document information"}, 500

    object = json.loads(json.dumps(res.json()), object_hook=lambda d: SimpleNamespace(**d)).object
    
    with open(file_path, "rb") as f:
        pdf_data = f.read()

    # Check for hash validity
    if partial_md5 != hashlib.md5(pdf_data).hexdigest()[:8]:
        return {"error": "ID not found"}, 404

    response = app.response_class(
        response=pdf_data,
        status=200,
        mimetype='application/pdf',
    )
    response.headers.set('Content-Disposition', 'attachment', filename=f'{object.name} - signed.pdf')
    return response


if __name__ == '__main__':
    if DEBUG:
        app.config["TEMPLATES_AUTO_RELOAD"] = True
        app.run(host="0.0.0.0", port=8081, debug=DEBUG)
    else:
        serve(app, host="0.0.0.0", port="8081")
