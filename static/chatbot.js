const chatArea = document.getElementById('chat-area');
const chatInput = document.getElementById('chat-input');
const chatForm = document.getElementById('chat-input-bar');
const sendBtn = document.getElementById('send-btn');
const loader = document.getElementById('loader');

let onboardingStep = 0;
let profile = {};
let onboardingActive = true;
let userName = '';

const USER_NAME = 'Olivia';
const USER_AVATAR = 'https://randomuser.me/api/portraits/women/44.jpg';
const BOT_NAME = 'AGENT X';
const BOT_AVATAR = `<span class="bot-avatar"><img src="https://cdn-icons-png.flaticon.com/512/3774/3774299.png" alt="Doctor" style="width:38px;height:38px;border-radius:50%;object-fit:cover;border:2px solid #e3eaf2;background:#e3f2fd;" /></span>`;

const ONBOARDING_QUESTIONS = [
  {
    key: 'name',
    icon: '👤',
    question: 'What is your name?',
    type: 'input',
    placeholder: 'Enter your name...'
  },
  {
    key: 'email',
    icon: '✉️',
    question: 'What is your email address?',
    type: 'input',
    placeholder: 'Enter your email...'
  },
  {
    key: 'gender',
    icon: '🚻',
    question: 'What is your gender?',
    options: ['Male', 'Female', 'Other', 'Prefer not to say']
  },
  {
    key: 'age',
    icon: '🎂',
    question: 'What is your age group?',
    options: ['Under 18', '18-29', '30-44', '45-59', '60+']
  },
  {
    key: 'conditions',
    icon: '💊',
    question: 'Do you have any existing health conditions?',
    options: ['None', 'Diabetes', 'Hypertension', 'Asthma', 'Heart Disease', 'Other']
  },
  {
    key: 'lifestyle',
    icon: '🏃',
    question: 'How would you describe your lifestyle?',
    options: ['Active', 'Moderate', 'Sedentary', 'Prefer not to say']
  }
];

function askOnboardingQuestion() {
  if (onboardingStep < ONBOARDING_QUESTIONS.length) {
    const q = ONBOARDING_QUESTIONS[onboardingStep];
    // Bot asks the question
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-bubble bot-msg';
    msgDiv.innerHTML = `
      ${BOT_AVATAR}
      <div>
        <div class="name-label">${BOT_NAME}</div>
        <div class="bubble-content"></div>
      </div>
    `;
    chatArea.appendChild(msgDiv);
    const bubble = msgDiv.querySelector('.bubble-content');
    let i = 0;
    function type() {
      if (i <= q.question.length) {
        bubble.innerHTML = q.question.slice(0, i) + '<span class="typewriter-cursor">|</span>';
        chatArea.scrollTop = chatArea.scrollHeight;
        i++;
        setTimeout(type, 5 + Math.random()*24);
      } else {
        bubble.innerHTML = q.question;
        // After typing, show options or input
        if (q.type === 'input') {
          const inputDiv = document.createElement('div');
          inputDiv.style.display = 'flex';
          inputDiv.style.gap = '10px';
          inputDiv.style.marginTop = '10px';
          const input = document.createElement('input');
          input.type = 'text';
          input.placeholder = q.placeholder || '';
          input.className = 'onboarding-input';
          input.style.flex = '1';
          input.autofocus = true;
          input.onkeydown = (e) => {
            if (e.key === 'Enter') {
              submitName();
            }
          };
          inputDiv.appendChild(input);
          const btn = document.createElement('button');
          btn.className = 'onboarding-btn';
          btn.innerText = 'Continue';
          btn.onclick = submitName;
          inputDiv.appendChild(btn);
          bubble.appendChild(inputDiv);
          input.focus();
          function submitName() {
            const val = input.value.trim();
            if (!val) return;
            profile[q.key] = val;
            if (q.key === 'name') {
              userName = val;
            }
            window.updateProfile(profile);
            renderUserMessage(val);
            onboardingStep++;
            askOnboardingQuestion();
          }
        } else {
          const optsDiv = document.createElement('div');
          optsDiv.className = 'onboarding-options';
          optsDiv.style.marginTop = '10px';
          q.options.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'onboarding-btn';
            btn.innerText = opt;
            btn.onclick = () => {
              profile[q.key] = opt;
              window.updateProfile(profile);
              renderUserMessage(opt);
              onboardingStep++;
              askOnboardingQuestion();
            };
            optsDiv.appendChild(btn);
          });
          bubble.appendChild(optsDiv);
        }
      }
    }
    type();
  } else {
    onboardingActive = false;
    chatInput.disabled = false;
    chatInput.placeholder = 'Type your message...';
    typewriterBotMsg(`Thank you${userName ? ', ' + userName : ''}! Your health profile is ready. How can I assist you today?`);
  }
}

function typewriterBotMsg(text) {
  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-bubble bot-msg';
  msgDiv.innerHTML = `
    ${BOT_AVATAR}
    <div>
      <div class="name-label">${BOT_NAME}</div>
      <div class="bubble-content"></div>
    </div>
  `;
  chatArea.appendChild(msgDiv);
  const bubble = msgDiv.querySelector('.bubble-content');
  // Use marked to convert markdown to HTML
  const html = marked.parse(text);
  // Typewriter effect for HTML: reveal one character at a time, but don't break tags
  let i = 0;
  function type() {
    // Show up to i-th character of the HTML string
    let partial = html.slice(0, i);
    bubble.innerHTML = partial + '<span class="typewriter-cursor">|</span>';
    chatArea.scrollTop = chatArea.scrollHeight;
    i++;
    if (i <= html.length) {
      setTimeout(type, 5 + Math.random()*24);
    } else {
      bubble.innerHTML = html;
      attachBookAppointmentHandlers(); // Attach handlers after rendering
    }
  }
  type();
}

chatForm.onsubmit = async (e) => {
  e.preventDefault();
  if (onboardingActive) return;
  const msg = chatInput.value.trim();
  if (!msg) return;
  renderUserMessage(msg);
  chatInput.value = '';
  showLoader(true);
  fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: msg, history: []})
  })
  .then(res => res.json())
  .then(data => {
    typewriterBotMsg(data.response);
    showLoader(false);
  })
  .catch(() => {
    typewriterBotMsg('Sorry, there was a problem connecting to the server.');
    showLoader(false);
  });
};

function renderUserMessage(text, time = null) {
  const initial = (userName && userName.length > 0) ? userName[0].toUpperCase() : 'Y';
  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-bubble user-msg';
  msgDiv.innerHTML = `
    <span class="avatar" style="background:#e3f2fd;color:#2563eb;font-weight:600;font-size:1.2rem;display:flex;align-items:center;justify-content:center;">${initial}</span>
    <div>
      <div class="name-label">You</div>
      <div class="bubble-content">${text}</div>
    </div>
  `;
  chatArea.appendChild(msgDiv);
  chatArea.scrollTop = chatArea.scrollHeight;
}

function showLoader(show = true) {
  loader.style.display = show ? 'flex' : 'none';
}

// Override onboarding logic
chatInput.disabled = true;
chatInput.placeholder = 'Please answer the onboarding questions...';
askOnboardingQuestion();

function attachBookAppointmentHandlers() {
  document.querySelectorAll('.book-btn').forEach(btn => {
    btn.onclick = function() {
      const providerName = btn.getAttribute('data-provider');
      const providerEmail = btn.getAttribute('data-email');
      showBookingForm(providerName, providerEmail);
    };
  });
}

// Call this after every bot message is rendered:
setTimeout(attachBookAppointmentHandlers, 100); // or after your render function

function showBookingForm(providerName, providerEmail) {
  // Remove any existing form
  const oldForm = document.getElementById('booking-form-modal');
  if (oldForm) oldForm.remove();

  // Create form HTML
  const formDiv = document.createElement('div');
  formDiv.id = 'booking-form-modal';
  formDiv.style = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;z-index:9999;';
  formDiv.innerHTML = `
    <form id="booking-form" style="background:#fff;padding:24px 32px;border-radius:12px;box-shadow:0 2px 16px #0002;min-width:320px;max-width:90vw;">
      <h3>Book Appointment with ${providerName}</h3>
      <input type="hidden" name="provider_email" value="${providerEmail}" />
      <div style="margin-bottom:10px;"><input name="name" placeholder="Your Name" required style="width:100%;padding:8px;" /></div>
      <div style="margin-bottom:10px;"><input name="email" placeholder="Your Email" type="email" required style="width:100%;padding:8px;" /></div>
      <div style="margin-bottom:10px;"><input name="phone" placeholder="Your Phone" required style="width:100%;padding:8px;" /></div>
      <div style="margin-bottom:10px;"><input name="date" type="date" required style="width:100%;padding:8px;" /></div>
      <div style="margin-bottom:10px;"><input name="time" type="time" required style="width:100%;padding:8px;" /></div>
      <div style="margin-bottom:10px;"><textarea name="notes" placeholder="Notes (optional)" style="width:100%;padding:8px;"></textarea></div>
      <button type="submit" style="background:#2563eb;color:#fff;padding:8px 16px;border:none;border-radius:6px;">Book</button>
      <button type="button" onclick="document.getElementById('booking-form-modal').remove()" style="margin-left:10px;">Cancel</button>
    </form>
  `;
  document.body.appendChild(formDiv);

  document.getElementById('booking-form').onsubmit = async function(e) {
    e.preventDefault();
    const form = e.target;
    const booking = {
      name: form.name.value,
      email: form.email.value,
      phone: form.phone.value,
      date: form.date.value,
      time: form.time.value,
      notes: form.notes.value,
    };
    // Send to backend
    const res = await fetch('/api/book', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ booking })
    });
    const data = await res.json();
    alert((data.provider_result || data.error || '') + '\n' + (data.user_result || ''));
    formDiv.remove();
  };
} 