const navbarMenu = document.querySelector(".navbar .links");
const menuBtn = document.querySelector(".menu-btn");
const hideMenuBtn = navbarMenu.querySelector(".close-btn");
const showPopupBtn = document.querySelector(".login-btn");
const formPopup = document.querySelector(".form-popup");
const feedbackForm = document.getElementById('feedbackForm')
const hidePopupBtn = document.querySelector(".form-popup .close-btn");

menuBtn.addEventListener("click", () => {
  navbarMenu.classList.toggle("show-menu");
});

hideMenuBtn.addEventListener("click", () => menuBtn.click());

if (showPopupBtn) {
  showPopupBtn.addEventListener("click", () => {
    document.body.classList.toggle("show-popup");
  });
}

hidePopupBtn.addEventListener("click", () => showPopupBtn.click());

var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function () {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  });
}

var textarea = document.getElementById("textarea");
var heightLimit = 200;

if (textarea) {
  textarea.oninput = function () {
    textarea.style.height = "";
    textarea.style.height = Math.min(textarea.scrollHeight, heightLimit) + "px";
  };
}

// Обработка отправки формы для входа
document.getElementById('loginForm').addEventListener('submit', function (event) {
  event.preventDefault();
  // Получаем данные формы для входа и отправляем на сервер
  var formData = new FormData(this);

  fetch('/login', {
    method: 'POST',
    body: formData
  })
    .then(response => response.text())
    .then(data => {
      if (data.includes('OK')) {
        location.reload();
      }
      else {
        var errorData = JSON.parse(data);
        var errorMessage = errorData.error
        var errorBlock = document.getElementById('error');
        errorBlock.style.display = 'block';
        errorBlock.innerHTML = '<strong>Ошибка:</strong> ' + errorMessage;
      }
    })
});

// Обработка отправки формы обратной связи
if (feedbackForm) {
  feedbackForm.addEventListener('submit', function (event) {
    event.preventDefault();
    // Получаем данные формы для обратной связи
    var formData = new FormData(this);

    // Получаем параметры запроса из URL
    var urlParams = new URLSearchParams(window.location.search);
    var user_id = urlParams.get('user_id');
    var lab_id = urlParams.get('lab_id');

    // Добавляем параметры запроса к данным формы
    formData.append('user_id', user_id);
    formData.append('lab_id', lab_id);

    // Отправляем данные на сервер
    fetch('/feedback', {
      method: 'POST',
      body: formData
    })
      .then(response => response.text())
      .then(data => {
        location.reload();
      })
  });
}
