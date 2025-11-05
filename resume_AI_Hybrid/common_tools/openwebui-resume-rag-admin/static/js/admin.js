// JavaScript functions for the admin interface of the OpenWebUI Resume RAG System

document.addEventListener("DOMContentLoaded", function() {
    const createButton = document.getElementById("create-collection");
    const deleteButton = document.getElementById("delete-collection");
    const clearButton = document.getElementById("clear-contents");
    const listButton = document.getElementById("list-collections");
    const statsButton = document.getElementById("display-stats");

    createButton.addEventListener("click", function() {
        const collectionName = document.getElementById("collection-name").value;
        if (collectionName) {
            fetch('/admin/create_collection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: collectionName })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.success) {
                    document.getElementById("collection-name").value = '';
                }
            });
        } else {
            alert("Please enter a collection name.");
        }
    });

    deleteButton.addEventListener("click", function() {
        const collectionName = document.getElementById("collection-name").value;
        if (collectionName) {
            fetch('/admin/delete_collection', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: collectionName })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.success) {
                    document.getElementById("collection-name").value = '';
                }
            });
        } else {
            alert("Please enter a collection name.");
        }
    });

    clearButton.addEventListener("click", function() {
        fetch('/admin/clear_contents', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
        });
    });

    listButton.addEventListener("click", function() {
        fetch('/admin/list_collections')
        .then(response => response.json())
        .then(data => {
            const listContainer = document.getElementById("collection-list");
            listContainer.innerHTML = '';
            data.collections.forEach(collection => {
                const listItem = document.createElement("li");
                listItem.textContent = collection;
                listContainer.appendChild(listItem);
            });
        });
    });

    statsButton.addEventListener("click", function() {
        fetch('/admin/display_stats')
        .then(response => response.json())
        .then(data => {
            const statsContainer = document.getElementById("stats-display");
            statsContainer.innerHTML = `
                <p>Total Collections: ${data.totalCollections}</p>
                <p>Total Documents: ${data.totalDocuments}</p>
                <p>Database Size: ${data.databaseSize} MB</p>
            `;
        });
    });
});