

// Outline list
export function buildOutlineList(items, container, pdfInstance, renderPageFunction) {

  Array.from(items).forEach(item => {
    const li = document.createElement('li');
    li.classList.add('pdf-outline-item');

    const toggle = document.createElement('span');
    toggle.textContent = item.items && item.items.length > 0 ? '+' : '';
    toggle.classList.add('toggle-icon');

    const title = document.createElement('span');
    title.textContent = item.title;
    title.style.cursor = 'pointer';

    // Click to navigate to page
    title.addEventListener('click', () => {
      pdfInstance.getDestination(item.dest).then(dest => {
        const ref = dest[0];
        pdfInstance.getPageIndex(ref).then(pageIndex => {
          const pageNumber = pageIndex + 1;
          renderPageFunction(pageNumber); 
        });
      });
    });

    li.appendChild(toggle);
    li.appendChild(title);

    // Handle nested items
    if (item.items && item.items.length > 0) {
      const subList = document.createElement('ul');
      subList.classList.add('pdf-outline-list', 'hidden');

      buildOutlineList(item.items, subList);
      li.appendChild(subList);

      toggle.addEventListener('click', () => {
        subList.classList.toggle('hidden');
        toggle.textContent = subList.classList.contains('hidden') ? '+' : '−';
      });
    }

    container.appendChild(li);
  });
}
