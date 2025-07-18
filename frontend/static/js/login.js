document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
  
    form.addEventListener("submit", (e) => {
      const username = document.querySelector("#username").value.trim();
      const password = document.querySelector("#password").value.trim();
  
      if (!username || !password) {
        e.preventDefault();
        alert("Please fill in both username and password.");
      }
    });
  });
  