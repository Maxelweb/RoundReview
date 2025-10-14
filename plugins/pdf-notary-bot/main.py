import os, json, io
import base64
import requests
from types import SimpleNamespace
from flask import Flask, request, jsonify
from pyhanko.sign import SimpleSigner, sign_pdf, PdfSignatureMetadata
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from config import (
    log,
    DEBUG,
    API_BASE_URL, 
    API_KEY,
    PLUGIN_CERT_PATH, 
    PLUGIN_KEY_PATH,
    PLUGIN_KEY_PASSPHRASE,
    PLUGIN_NAME,
    PLUGIN_BASE_URL,
    PLUGIN_SIGNED_PDFS_FOLDER
)

app = Flask(__name__)

def build_signer() -> SimpleSigner:
    """ Build a Simple Signer based on the provided certificates """
    signer = SimpleSigner.load(
        key_file=PLUGIN_KEY_PATH,
        cert_file=PLUGIN_CERT_PATH,
        key_passphrase=PLUGIN_KEY_PASSPHRASE,
    )
    return signer

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

    # load json object into a SimpleNamespace
    object = json.loads(json.dumps(res.json()), object_hook=lambda d: SimpleNamespace(**d)).object
    
    if "NO_SIGNATURE" in object.description: 
        if status != "Approved":
            log.warning("Notification valid, but NO_SIGNATURE found in description. Aborted.")
            return {"message": "Notification valid, but NO_SIGNATURE found in description. Aborted."}, 200
    
    signed_pdf = sign_pdf(
        IncrementalPdfFileWriter(io.BytesIO(base64.urlsafe_b64decode(object.raw))),
        signer=build_signer(),
        signature_meta=PdfSignatureMetadata(field_name='Signature1'),
    )

    output_path = f"signed_pdfs/{object_id}.pdf"
    with open(output_path, "wb") as f:
        f.write(signed_pdf.getbuffer())

    log.info("Saved PDF for Object ID = %s and Project ID = ", object_id, project_id)

    encoded_object = str(base64.urlsafe_b64encode(bytes(object_id, "utf-8")))

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


@app.route('/download/<base64_object_id>', methods=['GET'])
def handle_download(base64_object_id:str):
    """ Handle Download of the stored signed pdf file """
    try:
        object_id = base64.urlsafe_b64decode(base64_object_id).decode("utf-8")
    except Exception as e:
        log.error("Error decoding base64 object ID: %s", e)
        return {"error": "Invalid ID"}, 400

    file_path = f"{PLUGIN_SIGNED_PDFS_FOLDER}/{object_id}.pdf"
    if not os.path.exists(file_path):
        return {"error": "File not found"}, 404

    res = requests.get(
        url=f"{API_BASE_URL}/objects/{object_id}", 
        headers={"x-api-key": API_KEY}
    )

    if res.status_code != 200:
        return {"error": "Failed to fetch PDF information"}, 500

    object = res.json().object

    with open(file_path, "rb") as f:
        pdf_data = f.read()

    response = app.response_class(
        response=pdf_data,
        status=200,
        mimetype='application/pdf',
    )
    response.headers.set('Content-Disposition', 'attachment', filename=f'{object.name} - signed.pdf')
    return response

if __name__ == '__main__':
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(host="0.0.0.0", port=8081, debug=DEBUG)
