// page.html writes the public API base into a json_script tag with id api-base.
document.getElementById('api').textContent = JSON.parse(document.getElementById('api-base').textContent);
