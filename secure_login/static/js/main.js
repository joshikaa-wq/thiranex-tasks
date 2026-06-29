// Toggle password visibility
function togglePwd(inputId, iconId) {
  const inp = document.getElementById(inputId);
  const ico = document.getElementById(iconId);
  if (inp.type === 'password') {
    inp.type = 'text';
    ico.classList.replace('fa-eye', 'fa-eye-slash');
  } else {
    inp.type = 'password';
    ico.classList.replace('fa-eye-slash', 'fa-eye');
  }
}

// Password strength meter
const pwdInput = document.getElementById('password');
if (pwdInput) {
  pwdInput.addEventListener('input', () => {
    const val = pwdInput.value;
    let score = 0;
    if (val.length >= 8)  score++;
    if (val.length >= 12) score++;
    if (/[A-Z]/.test(val)) score++;
    if (/[0-9]/.test(val)) score++;
    if (/[^A-Za-z0-9]/.test(val)) score++;

    const fill = document.getElementById('strengthFill');
    const text = document.getElementById('strengthText');
    if (!fill) return;

    const levels = [
      { pct: 0,   cls: 'bg-danger',  label: '' },
      { pct: 20,  cls: 'bg-danger',  label: 'Very Weak 🔴' },
      { pct: 40,  cls: 'bg-warning', label: 'Weak 🟠' },
      { pct: 60,  cls: 'bg-info',    label: 'Fair 🟡' },
      { pct: 80,  cls: 'bg-primary', label: 'Strong 🔵' },
      { pct: 100, cls: 'bg-success', label: 'Very Strong 🟢' },
    ];
    const l = levels[score];
    fill.style.width = l.pct + '%';
    fill.className = 'progress-bar ' + l.cls;
    text.textContent = l.label;
  });
}

// Auto-dismiss alerts after 4s
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => {
      el.classList.remove('show');
      setTimeout(() => el.remove(), 300);
    }, 4000);
  });
});
