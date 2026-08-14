const API_URL = "http://127.0.0.1:8000";


/* =========================
   LOGIN
========================= */

const loginForm =
    document.getElementById("login-form");

if (loginForm) {

    loginForm.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();

            const email =
                document.getElementById("email").value;

            const password =
                document.getElementById("password").value;


            const formData =
                new URLSearchParams();

            formData.append(
                "username",
                email
            );

            formData.append(
                "password",
                password
            );


            try {

                const response =
                    await fetch(
                        `${API_URL}/auth/login`,
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/x-www-form-urlencoded"
                            },

                            body: formData
                        }
                    );


                if (!response.ok) {

                    const data =
                        await response.json();

                    throw new Error(
                        data.detail ||
                        "Login failed"
                    );

                }


                const data =
                    await response.json();


                localStorage.setItem(
                    "access_token",
                    data.access_token
                );


                window.location.href =
                    "index.html";

            } catch (error) {

                document
                    .getElementById("login-error")
                    .textContent =
                    error.message;

            }

        }
    );

}


/* =========================
   GLOBAL VARIABLES
========================= */

let clothes = [];

let selectedCategory = "all";

let editingClothingId = null;

/* =========================
   ELEMENTS
========================= */

const grid =
    document.getElementById("clothing-grid");

const emptyState =
    document.getElementById("empty-state");

const modal =
    document.getElementById("modal");

const addButton =
    document.getElementById("add-btn");

const emptyAddButton =
    document.getElementById("empty-add-btn");

const closeModal =
    document.getElementById("close-modal");

const form =
    document.getElementById("clothing-form");

const logoutButton =
    document.getElementById("logout-btn");


/* =========================
   TOKEN
========================= */

function getToken() {

    return localStorage.getItem(
        "access_token"
    );

}


/* =========================
   LOAD CLOTHING
========================= */

async function loadClothes() {

    const token = getToken();


    if (!token) {

        window.location.href =
            "login.html";

        return;

    }


    try {

        const response =
            await fetch(
                `${API_URL}/clothing-items/`,
                {
                    headers: {
                        Authorization:
                            `Bearer ${token}`
                    }
                }
            );


        if (response.status === 401) {

            logout();

            return;

        }


        if (!response.ok) {

            throw new Error(
                "Failed to load clothing"
            );

        }


        clothes =
            await response.json();


        renderClothes();


    } catch (error) {

        console.error(error);


        if (grid) {

            grid.innerHTML = `
                <p>
                    Could not connect to backend.
                </p>
            `;

        }

    }

}


/* =========================
   RENDER
========================= */

function renderClothes() {

    // This function only belongs to the wardrobe page
    if (!grid || !emptyState) {
        return;
    }


    let filtered = clothes;


    if (selectedCategory !== "all") {

        filtered =
            clothes.filter(
                (item) =>
                    item.category.toLowerCase()
                    === selectedCategory
            );

    }


    grid.innerHTML = "";


    if (filtered.length === 0) {

        emptyState.classList.remove(
            "hidden"
        );

        return;

    }


    emptyState.classList.add(
        "hidden"
    );


    filtered.forEach(
        (item) => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "clothing-card";


            card.innerHTML = `

                <div class="clothing-image">
                    ${
                        item.image_url
                            ? `<img src="${API_URL}${item.image_url}" alt="${item.name}">`
                            : "👕"
                    }
                </div>

                <div class="clothing-info">

                    <h3>
                        ${item.name}
                    </h3>

                    <p class="clothing-category">
                        ${item.category}
                    </p>

                    <p class="clothing-color">
                        ${item.color}
                    </p>

                    <button
                        class="edit-btn"
                        data-id="${item.id}"
                    >
                        Edit
                    </button>

                    <button
                        class="delete-btn"
                        data-id="${item.id}"
                    >
                        Delete
                    </button>

                </div>

            `;


            grid.appendChild(card);

            const editButton =
                    card.querySelector(".edit-btn");
            editButton.addEventListener(
                "click",
                ()=>{
                    openEditModal(item);
                }
            );

            const deleteButton =
                card.querySelector(".delete-btn");

            deleteButton.addEventListener(
                "click",
                () => {
                    deleteClothing(item.id);
                }
            );

        }
    );

}

/* =========================
   delete
========================= */
async function deleteClothing(clothingId) {

    const token = getToken();

    if (!token) {
        window.location.href = "login.html";
        return;
    }

    const confirmed =
        confirm("Are you sure you want to delete this clothing item?");

    if (!confirmed) {
        return;
    }

    try {

        const response = await fetch(
            `${API_URL}/clothing-items/${clothingId}`,
            {
                method: "DELETE",

                headers: {
                    Authorization:
                        `Bearer ${token}`
                }
            }
        );

        if (response.status === 401) {

            logout();

            return;
        }

        if (!response.ok) {

            throw new Error(
                "Failed to delete clothing"
            );
        }

        await loadClothes();

    } catch (error) {

        console.error(error);

        alert(error.message);

    }
}


/* =========================
   CATEGORY FILTER
========================= */

document
    .querySelectorAll(".category")
    .forEach(
        (button) => {

            button.addEventListener(
                "click",
                () => {

                    document
                        .querySelectorAll(
                            ".category"
                        )
                        .forEach(
                            (btn) =>
                                btn.classList
                                    .remove(
                                        "active"
                                    )
                        );


                    button.classList.add(
                        "active"
                    );


                    selectedCategory =
                        button.dataset.category;


                    renderClothes();

                }
            );

        }
    );


/* =========================
   MODAL
========================= */

function openModal() {

    if (!modal) {
        return;
    }


    modal.classList.remove(
        "hidden"
    );

}


function closeModalWindow() {

    if (!modal) {
        return;
    }


    modal.classList.add(
        "hidden"
    );

}
function openEditModal(item) {

    if (!modal || !form) {
        return;
    }

    editingClothingId = item.id;

    document.querySelector(
        ".modal-header h2"
    ).textContent = "Edit Clothing";

    document.querySelector(
        ".submit-btn"
    ).textContent = "Save Changes";

    document.getElementById(
        "name"
    ).value = item.name;

    document.getElementById(
        "category"
    ).value = item.category;

    document.getElementById(
        "color"
    ).value = item.color;

    document.getElementById(
        "form-error"
    ).textContent = "";

    modal.classList.remove("hidden");
}


if (addButton) {

    addButton.addEventListener(
        "click",
        openModal
    );

}


if (emptyAddButton) {

    emptyAddButton.addEventListener(
        "click",
        openModal
    );

}


if (closeModal) {

    closeModal.addEventListener(
        "click",
        closeModalWindow
    );

}


/* =========================
   ADD CLOTHING
========================= */

if (form) {

    form.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();

            const token = getToken();

            if (!token) {
                window.location.href = "login.html";
                return;
            }

            const name =
                document.getElementById("name").value;

            const category =
                document.getElementById("category").value;

            const color =
                document.getElementById("color").value;


            try {

                let response;


                // =========================
                // EDIT
                // =========================

                if (editingClothingId) {

                    response = await fetch(
                        `${API_URL}/clothing-items/${editingClothingId}`,
                        {
                            method: "PUT",

                            headers: {
                                "Content-Type":
                                    "application/json",

                                Authorization:
                                    `Bearer ${token}`
                            },

                            body: JSON.stringify({
                                name: name,
                                category: category,
                                color: color
                            })
                        }
                    );

                }


                // =========================
                // ADD
                // =========================

                else {

                    const formData =
                        new FormData(form);

                    response = await fetch(
                        `${API_URL}/clothing-items/`,
                        {
                            method: "POST",

                            headers: {
                                Authorization:
                                    `Bearer ${token}`
                            },

                            body: formData
                        }
                    );

                }


                // =========================
                // RESPONSE
                // =========================

                if (response.status === 401) {

                    logout();

                    return;

                }


                if (!response.ok) {

                    const data =
                        await response.json();

                    throw new Error(
                        JSON.stringify(
                            data.detail ||
                            "Failed to save clothing",
                            null,
                            2
                        )
                    );

                }


                // Reset edit state

                editingClothingId = null;


                // Reset form

                form.reset();


                // Restore modal to Add mode

                document.querySelector(
                    ".modal-header h2"
                ).textContent =
                    "Add Clothing";

                document.querySelector(
                    ".submit-btn"
                ).textContent =
                    "Add Clothing";


                document.getElementById(
                    "form-error"
                ).textContent = "";


                closeModalWindow();


                // Reload wardrobe

                await loadClothes();

            }


            catch (error) {

                const formError =
                    document.getElementById(
                        "form-error"
                    );

                if (formError) {

                    formError.textContent =
                        error.message;

                }

            }

        }
    );

}

/* =========================
   LOGOUT
========================= */

if (logoutButton) {

    logoutButton.addEventListener(
        "click",
        logout
    );

}


function logout() {

    localStorage.removeItem(
        "access_token"
    );


    window.location.href =
        "login.html";

}


/* =========================
   START
========================= */

// Only load wardrobe data
// when we are actually on the wardrobe page.

if (grid) {

    loadClothes();

}