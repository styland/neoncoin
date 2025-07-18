document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
  
    form.addEventListener("submit", (e) => {
      const name = document.querySelector("#username").value.trim();
      const email = document.querySelector("#email").value.trim();
      const password = document.querySelector("#password").value.trim();
      const confirmPassword = document.querySelector("#confirm_password").value.trim();
  
      // Check if fields are empty
      if (!name || !email || !password || !confirmPassword) {
        e.preventDefault();
        alert("Please fill in all fields.");
        return;
      }
  
      // Check username length
      if (name.length < 3) {
        e.preventDefault();
        alert("Username must be at least 3 characters long.");
        return;
      }
  
      // Check password length
      if (password.length < 6) {
        e.preventDefault();
        alert("Password must be at least 6 characters long.");
        return;
      }
  
      // Check if passwords match
      if (password !== confirmPassword) {
        e.preventDefault();
        alert("Passwords do not match.");
        return;
      }
    });
  });
  