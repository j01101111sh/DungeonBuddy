document.addEventListener('DOMContentLoaded', function() {
    // Add Link
    const addLinkForm = document.getElementById('add-link-form');
    if (addLinkForm) {
      addLinkForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(addLinkForm);
        const url = addLinkForm.action;
        const csrfToken = formData.get('csrfmiddlewaretoken');

        fetch(url, {
            method: 'POST',
            body: new URLSearchParams(formData),
            headers: {
              'X-CSRFToken': csrfToken,
              'Content-Type': 'application/x-www-form-urlencoded',
              'X-Requested-With': 'XMLHttpRequest'
            },
          })
          .then(response => response.json())
          .then(data => {
            if (data.pk) {
              const newLink = `
                        <li id="link-${data.pk}" class="list-group-item d-flex justify-content-between align-items-center">
                            <a href="${data.url}" target="_blank">${data.name}</a>
                            <button class="btn btn-sm btn-outline-danger delete-link-btn" data-link-pk="${data.pk}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </li>`;
              const list = document.getElementById('helpful-links-list');
              list.insertAdjacentHTML('beforeend', newLink);
              addLinkForm.reset();
              // Hide the 'No helpful links yet' message if it exists
              const noLinksMessage = document.getElementById('no-links-message');
              if (noLinksMessage) {
                noLinksMessage.classList.add('hidden');
              }
            } else if (data.errors) {
              const errorDiv = document.getElementById('add-link-errors');
              let errorMessages = '';
              for (const field in data.errors) {
                errorMessages += `<p>${field}: ${data.errors[field].join(', ')}</p>`;
              }
              errorDiv.innerHTML = errorMessages;
              errorDiv.classList.remove('hidden');
            }
          })
          .catch(error => console.error('Error adding link:', error));
      });
    }

    // Delete Link
    document.getElementById('helpful-links-list').addEventListener('click', function(e) {
      const deleteButton = e.target.closest('.delete-link-btn');
      if (deleteButton) {
        const linkPk = deleteButton.dataset.linkPk;
        const url = `/links/${linkPk}/delete/`;
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        if (confirm('Are you sure you want to delete this link?')) {
          fetch(url, {
              method: 'POST',
              headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
              },
            })
            .then(response => {
              if (response.ok) {
                document.getElementById(`link-${linkPk}`).remove();
                const list = document.getElementById('helpful-links-list');
                if (list.children.length === 0) {
                  const noLinksMessage = document.getElementById('no-links-message');
                  if (noLinksMessage) {
                    noLinksMessage.classList.remove('hidden');
                  }
                }
              } else {
                console.error('Failed to delete link');
              }
            })
            .catch(error => console.error('Error deleting link:', error));
        }
      }
    });
  });
