document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('swanForm');
    form.addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent the default form submission

        const formData = new FormData(form);
        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Device added successfully!');
                updateDeviceList(data.devices); // Update the device list
                form.reset(); // Reset the form
            } else {
                alert('Failed to add device.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while adding the device.');
        });
    });
});

function deleteDevice(imei) {
    if (confirm('Are you sure you want to delete this device?')) {
        fetch(`/delete/swan/${imei}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (response.ok) {
                alert('Device deleted successfully!');
                location.reload();
            } else {
                alert('Failed to delete device.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the device.');
        });
    }
}

function updateDeviceList(devices) {
    const imeiList = document.getElementById('imeiList');
    imeiList.innerHTML = ''; // Clear the current list

    devices.forEach(device => {
        const deviceItem = document.createElement('li');
        deviceItem.className = 'device-item';
        deviceItem.onclick = () => showDeviceDetails(device.imei);

        const deviceId = device.imei;

        deviceItem.textContent = deviceId;

        imeiList.appendChild(deviceItem);
    });
}

function showDeviceDetails(imei) {
    fetch(`/get_device_details/${imei}`)
    .then(response => response.json())
    .then(data => {
        const deviceDetails = document.getElementById('deviceDetails');
        if (data.success) {
            const device = data.device;
            deviceDetails.innerHTML = `
                <h2>Device ID: ${imei}</h2>
                <pre>${JSON.stringify(device, null, 2)}</pre>
                <button onclick="deleteDevice('${imei}')">Delete</button>
            `;
        } else {
            deviceDetails.innerHTML = '<p>Failed to load device details.</p>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const deviceDetails = document.getElementById('deviceDetails');
        deviceDetails.innerHTML = '<p>An error occurred while loading the device details.</p>';
    });
}