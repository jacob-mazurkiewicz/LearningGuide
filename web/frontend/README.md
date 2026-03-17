# 🎨 Web Frontend — HTML + CSS + JavaScript

The frontend is a **Single Page Application (SPA)** built with plain HTML, CSS, and JavaScript.
No build step required — just edit the files and refresh your browser!

## Files

| File | Purpose |
|------|---------|
| `index.html` | The HTML structure (one file for the whole app) |
| `style.css` | Custom CSS styles (Bootstrap 5 handles the rest) |
| `app.js` | All JavaScript logic — data fetching, UI updates, events |

## How a Single Page Application Works

Traditional websites load a new HTML page for every click.
SPAs load one HTML file and update only the parts that changed.

```
User clicks "Create Plan"
    → JavaScript calls POST /api/plans
    → API creates the plan in the database
    → API returns the new plan as JSON
    → JavaScript adds the plan to the sidebar list
    → No page reload! ✅
```

## External Libraries (loaded from CDN)

| Library | What It Does |
|---------|-------------|
| [Bootstrap 5](https://getbootstrap.com) | Buttons, forms, modals, grid layout |
| [Bootstrap Icons](https://icons.getbootstrap.com) | 1,800+ icons (used as `<i class="bi bi-NAME">`) |
| [SortableJS](https://sortablejs.github.io/Sortable/) | Drag-and-drop reordering |

These are loaded from a CDN (Content Delivery Network) — a remote server that
delivers the library files. No `npm install` needed!

## Key JavaScript Concepts

### async/await
JavaScript is **asynchronous** — when you make a network request, the browser
doesn't freeze and wait. Instead, it continues running other code.
`async/await` makes asynchronous code look synchronous and easier to read:

```javascript
// Without async/await (callback hell):
fetch('/api/plans').then(res => res.json()).then(plans => {
  fetch('/api/plans/1').then(res => res.json()).then(plan => {
    // nested callbacks get messy fast...
  });
});

// With async/await (clean and readable):
const plans = await GET('/api/plans');
const plan = await GET('/api/plans/1');
```

### The fetch() API
`fetch()` is the browser's built-in way to make HTTP requests:

```javascript
const response = await fetch('/api/plans', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ title: 'My Plan' }),
});
const newPlan = await response.json();
```

### DOM Manipulation
The DOM (Document Object Model) is the tree of HTML elements.
JavaScript can find and modify any element:

```javascript
// Find an element by its ID
const title = document.getElementById('plan-title-display');
// Change its text content
title.textContent = 'My New Plan';
// Add a CSS class
title.classList.add('text-success');
```

### Event Listeners
Code runs when users interact with the page:

```javascript
document.getElementById('save-plan-btn').addEventListener('click', savePlan);
// When user clicks the button, call the savePlan function
```

## XSS Security

Whenever you display user-provided text in the HTML, always use `escapeHtml()`:

```javascript
// UNSAFE — if title is "<script>alert('hacked')</script>" this would run!
element.innerHTML = plan.title;

// SAFE — escapeHtml converts < to &lt; etc., making it display as text
element.innerHTML = escapeHtml(plan.title);
```

This protects against **XSS (Cross-Site Scripting)** attacks.

## Making Changes

1. Edit `index.html`, `style.css`, or `app.js`
2. Refresh your browser at `http://localhost:8000`
3. Changes appear immediately!

For Python backend changes, the server auto-reloads thanks to `uvicorn --reload`.
