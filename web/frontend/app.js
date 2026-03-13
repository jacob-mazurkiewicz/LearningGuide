/**
 * app.js — LearningGuide Frontend Application
 * =============================================
 * This is a Single Page Application written in plain JavaScript (no framework).
 *
 * How a SPA works:
 *   - The browser loads index.html once.
 *   - JavaScript fetches data from the API (/api/...) and updates the DOM
 *     (the HTML elements on the page) without doing a full page reload.
 *   - User interactions (button clicks, drag-and-drop) trigger API calls
 *     which update both the server data and the visible UI.
 *
 * Key JavaScript concepts used here:
 *   - async/await: Modern way to handle asynchronous operations (API calls)
 *   - fetch(): Built-in browser function to make HTTP requests
 *   - template literals: Backtick strings that allow embedded expressions ${...}
 *   - Arrow functions: const fn = () => { ... }
 *   - DOM manipulation: document.getElementById(), element.innerHTML, etc.
 *   - Event listeners: element.addEventListener('click', handler)
 */

// =============================================================================
// API HELPER — Centralized fetch wrapper
// =============================================================================

/**
 * All API calls go through this function.
 * It adds default headers and throws an error for non-2xx responses.
 *
 * @param {string} path - API path, e.g. "/api/plans"
 * @param {object} options - fetch options (method, body, etc.)
 * @returns {Promise<any>} - Parsed JSON response, or null for 204 No Content
 */
async function api(path, options = {}) {
  const defaults = {
    headers: { "Content-Type": "application/json" },
  };
  const res = await fetch(path, { ...defaults, ...options });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  if (res.status === 204) return null;  // No Content (successful delete)
  return res.json();
}

// Shorthand helpers for common HTTP methods
const GET = (path) => api(path);
const POST = (path, body) => api(path, { method: "POST", body: JSON.stringify(body) });
const PUT = (path, body) => api(path, { method: "PUT", body: JSON.stringify(body) });
const DELETE = (path) => api(path, { method: "DELETE" });


// =============================================================================
// STATE — Application data
// =============================================================================

/**
 * Simple application state.
 * In a framework like React or Vue, this would be called "state" or "store".
 * Here we just use a plain object.
 */
const state = {
  plans: [],           // All plans (for sidebar)
  currentPlan: null,   // The plan currently being viewed
  editingGoalId: null, // Goal being edited (null = creating new)
  editingSubtaskId: null,
  editingTaskId: null,
  contextGoalId: null,    // Goal context for creating subtasks
  contextSubtaskId: null, // Subtask context for creating tasks
  aiGeneratedPlan: null,  // Holds AI-generated plan before user imports it
};


// =============================================================================
// BOOTSTRAP COMPONENTS — Grab references to modals and toasts
// =============================================================================

// Bootstrap Modal and Toast classes — initialized after DOM is ready
let planModal, goalModal, subtaskModal, taskModal, aiModal, toastEl;

function initBootstrapComponents() {
  planModal    = new bootstrap.Modal(document.getElementById("plan-modal"));
  goalModal    = new bootstrap.Modal(document.getElementById("goal-modal"));
  subtaskModal = new bootstrap.Modal(document.getElementById("subtask-modal"));
  taskModal    = new bootstrap.Modal(document.getElementById("task-modal"));
  aiModal      = new bootstrap.Modal(document.getElementById("ai-modal"));
  toastEl      = new bootstrap.Toast(document.getElementById("app-toast"), { delay: 3000 });
}


// =============================================================================
// NOTIFICATIONS — Show success/error toasts
// =============================================================================

function showToast(message, type = "success") {
  const toastDiv = document.getElementById("app-toast");
  const toastMsg = document.getElementById("toast-message");
  toastDiv.className = `toast align-items-center text-white border-0 bg-${type}`;
  toastMsg.textContent = message;
  toastEl.show();
}


// =============================================================================
// SIDEBAR — Plan list
// =============================================================================

async function loadPlans() {
  try {
    state.plans = await GET("/api/plans");
    renderSidebar();
  } catch (e) {
    showToast("Failed to load plans: " + e.message, "danger");
  }
}

function renderSidebar() {
  const list = document.getElementById("plan-list");
  const noMsg = document.getElementById("no-plans-msg");

  if (state.plans.length === 0) {
    list.innerHTML = "";
    list.appendChild(noMsg);
    noMsg.style.display = "block";
    return;
  }

  noMsg.style.display = "none";
  list.innerHTML = "";

  for (const plan of state.plans) {
    const li = document.createElement("li");
    li.innerHTML = `
      <a href="#" class="nav-link ${state.currentPlan?.id === plan.id ? "active" : ""}"
         data-plan-id="${plan.id}">
        <i class="bi bi-journal-bookmark me-2"></i>${escapeHtml(plan.title)}
      </a>
    `;
    li.querySelector("a").addEventListener("click", (e) => {
      e.preventDefault();
      selectPlan(plan.id);
    });
    list.appendChild(li);
  }
}

async function selectPlan(planId) {
  try {
    state.currentPlan = await GET(`/api/plans/${planId}`);
    renderPlanView();
    renderSidebar();  // Update active state
  } catch (e) {
    showToast("Failed to load plan: " + e.message, "danger");
  }
}


// =============================================================================
// PLAN VIEW — Render the selected plan
// =============================================================================

function renderPlanView() {
  const plan = state.currentPlan;
  if (!plan) return;

  // Show plan view, hide welcome screen
  document.getElementById("welcome-screen").style.display = "none";
  document.getElementById("plan-view").style.display = "block";

  // Fill in plan header
  document.getElementById("plan-title-display").textContent = plan.title;
  document.getElementById("plan-desc-display").textContent = plan.description || "";

  // Calculate and display overall progress
  const allTasks = plan.goals.flatMap(g => g.subtasks.flatMap(s => s.daily_tasks));
  const totalTasks = allTasks.length;
  const doneTasks = allTasks.filter(t => t.completed).length;
  const pct = totalTasks > 0 ? Math.round(doneTasks / totalTasks * 100) : 0;

  document.getElementById("plan-progress-bar").style.width = `${pct}%`;
  document.getElementById("plan-progress-text").textContent =
    `${doneTasks}/${totalTasks} tasks (${pct}%)`;

  // Render goals
  renderGoals();
}

function renderGoals() {
  const container = document.getElementById("goals-container");
  const noGoalsMsg = document.getElementById("no-goals-msg");
  const goals = state.currentPlan.goals;

  if (goals.length === 0) {
    container.innerHTML = "";
    container.appendChild(noGoalsMsg);
    noGoalsMsg.style.display = "block";
    return;
  }

  noGoalsMsg.style.display = "none";
  container.innerHTML = "";

  for (const goal of goals) {
    const card = createGoalCard(goal);
    container.appendChild(card);
  }

  // Enable drag-and-drop reordering of goals
  Sortable.create(container, {
    animation: 150,
    handle: ".goal-drag-handle",
    ghostClass: "sortable-ghost",
    chosenClass: "sortable-chosen",
    onEnd: async (evt) => {
      const ids = [...container.querySelectorAll(".goal-card")].map(el => +el.dataset.goalId);
      try {
        await PUT(`/api/plans/${state.currentPlan.id}/goals/reorder`, { ids });
      } catch (e) {
        showToast("Reorder failed: " + e.message, "danger");
        await selectPlan(state.currentPlan.id);  // Refresh to correct order
      }
    },
  });
}

function createGoalCard(goal) {
  // Calculate goal progress
  const allTasks = goal.subtasks.flatMap(s => s.daily_tasks);
  const total = allTasks.length;
  const done = allTasks.filter(t => t.completed).length;
  const pct = total > 0 ? Math.round(done / total * 100) : 0;

  const div = document.createElement("div");
  div.className = "goal-card card";
  div.dataset.goalId = goal.id;

  div.innerHTML = `
    <div class="card-header d-flex align-items-start gap-2">
      <span class="goal-drag-handle drag-handle bi bi-grip-vertical fs-5 mt-1"></span>
      <div class="flex-grow-1 min-w-0">
        <div class="d-flex justify-content-between align-items-start">
          <h6 class="fw-bold mb-1 text-truncate" title="${escapeHtml(goal.title)}">
            ${escapeHtml(goal.title)}
          </h6>
          <div class="action-btn-group d-flex gap-1 ms-2 flex-shrink-0">
            <button class="btn btn-sm btn-outline-primary py-0 px-1 edit-goal-btn" title="Edit goal">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger py-0 px-1 delete-goal-btn" title="Delete goal">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
        ${goal.description ? `<p class="text-muted small mb-1">${escapeHtml(goal.description)}</p>` : ""}
        ${goal.start_date || goal.end_date ? `
          <p class="text-muted small mb-1">
            <i class="bi bi-calendar3 me-1"></i>
            ${goal.start_date || "?"} → ${goal.end_date || "?"}
          </p>
        ` : ""}
        <!-- Progress bar for this goal -->
        <div class="d-flex align-items-center gap-2 mt-1">
          <div class="progress flex-grow-1" style="height:6px">
            <div class="progress-bar bg-success" style="width:${pct}%"></div>
          </div>
          <small class="text-muted" style="width:40px; text-align:right">${pct}%</small>
        </div>
      </div>
    </div>
    <div class="card-body p-2">
      <!-- Subtasks list — populated below -->
      <div class="subtasks-list" data-goal-id="${goal.id}"></div>
      <!-- Add subtask button -->
      <button class="btn btn-sm btn-outline-secondary w-100 mt-2 add-subtask-btn" data-goal-id="${goal.id}">
        <i class="bi bi-plus me-1"></i>Add Subtask
      </button>
    </div>
  `;

  // Render subtasks inside this card
  const subtasksList = div.querySelector(".subtasks-list");
  for (const subtask of goal.subtasks) {
    subtasksList.appendChild(createSubtaskItem(subtask, goal));
  }

  // Enable drag-and-drop for subtasks within this goal
  Sortable.create(subtasksList, {
    animation: 150,
    handle: ".subtask-drag-handle",
    ghostClass: "sortable-ghost",
    onEnd: async () => {
      const ids = [...subtasksList.querySelectorAll(".subtask-item")].map(el => +el.dataset.subtaskId);
      try {
        await PUT(`/api/goals/${goal.id}/subtasks/reorder`, { ids });
      } catch (e) {
        showToast("Reorder failed: " + e.message, "danger");
        await selectPlan(state.currentPlan.id);
      }
    },
  });

  // Wire up edit/delete goal buttons
  div.querySelector(".edit-goal-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    openEditGoalModal(goal);
  });
  div.querySelector(".delete-goal-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    deleteGoal(goal.id);
  });
  div.querySelector(".add-subtask-btn").addEventListener("click", () => {
    openCreateSubtaskModal(goal.id);
  });

  return div;
}

function createSubtaskItem(subtask, goal) {
  // Calculate subtask progress
  const tasks = subtask.daily_tasks;
  const done = tasks.filter(t => t.completed).length;
  const pct = tasks.length > 0 ? Math.round(done / tasks.length * 100) : 0;

  const div = document.createElement("div");
  div.className = "subtask-item";
  div.dataset.subtaskId = subtask.id;

  const collapseId = `subtask-collapse-${subtask.id}`;

  div.innerHTML = `
    <div class="subtask-header d-flex align-items-center gap-2" data-bs-toggle="collapse"
         data-bs-target="#${collapseId}" aria-expanded="true">
      <span class="subtask-drag-handle drag-handle bi bi-grip-vertical small"></span>
      <div class="flex-grow-1 min-w-0">
        <div class="d-flex justify-content-between align-items-center">
          <span class="fw-semibold small text-truncate">${escapeHtml(subtask.title)}</span>
          <div class="d-flex align-items-center gap-1 ms-1 flex-shrink-0">
            <span class="badge bg-secondary rounded-pill">${done}/${tasks.length}</span>
            <div class="action-btn-group d-flex gap-1">
              <button class="btn btn-sm btn-outline-primary py-0 px-1 edit-subtask-btn" title="Edit">
                <i class="bi bi-pencil" style="font-size:0.7rem"></i>
              </button>
              <button class="btn btn-sm btn-outline-danger py-0 px-1 delete-subtask-btn" title="Delete">
                <i class="bi bi-trash" style="font-size:0.7rem"></i>
              </button>
            </div>
            <i class="bi bi-chevron-down small"></i>
          </div>
        </div>
        <div class="progress mt-1" style="height:4px">
          <div class="progress-bar bg-info" style="width:${pct}%"></div>
        </div>
      </div>
    </div>
    <div class="collapse show" id="${collapseId}">
      <div class="subtask-body">
        ${subtask.description ? `<p class="text-muted small mb-2">${escapeHtml(subtask.description)}</p>` : ""}
        <!-- Daily tasks list -->
        <div class="tasks-list" data-subtask-id="${subtask.id}">
          ${tasks.length === 0 ? '<p class="empty-state">No tasks yet</p>' : ""}
        </div>
        <button class="btn btn-sm btn-outline-secondary w-100 mt-2 add-task-btn"
                data-subtask-id="${subtask.id}">
          <i class="bi bi-plus me-1"></i>Add Daily Task
        </button>
      </div>
    </div>
  `;

  // Render daily tasks
  const tasksList = div.querySelector(".tasks-list");
  if (tasks.length > 0) {
    tasksList.innerHTML = "";
    for (const task of tasks) {
      tasksList.appendChild(createTaskItem(task));
    }
  }

  // Enable drag-and-drop for tasks within this subtask
  Sortable.create(tasksList, {
    animation: 150,
    handle: ".task-drag-handle",
    ghostClass: "sortable-ghost",
    onEnd: async () => {
      const ids = [...tasksList.querySelectorAll(".task-item")].map(el => +el.dataset.taskId);
      try {
        await PUT(`/api/subtasks/${subtask.id}/tasks/reorder`, { ids });
      } catch (e) {
        showToast("Reorder failed: " + e.message, "danger");
        await selectPlan(state.currentPlan.id);
      }
    },
  });

  // Wire up buttons
  div.querySelector(".edit-subtask-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    openEditSubtaskModal(subtask);
  });
  div.querySelector(".delete-subtask-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    deleteSubtask(subtask.id);
  });
  div.querySelector(".add-task-btn").addEventListener("click", () => {
    openCreateTaskModal(subtask.id);
  });

  return div;
}

function createTaskItem(task) {
  const div = document.createElement("div");
  div.className = `task-item ${task.completed ? "completed" : ""}`;
  div.dataset.taskId = task.id;

  // Format estimated time nicely
  const timeLabel = task.estimated_minutes >= 60
    ? `${(task.estimated_minutes / 60).toFixed(1)}h`
    : `${task.estimated_minutes}m`;

  div.innerHTML = `
    <span class="task-drag-handle bi bi-grip-vertical"></span>
    <input type="checkbox" class="task-checkbox" ${task.completed ? "checked" : ""}
           title="Mark as complete" />
    <span class="task-title">${escapeHtml(task.title)}</span>
    <div class="task-meta d-flex align-items-center gap-1">
      ${task.scheduled_date ? `<span class="badge bg-light text-dark border">${task.scheduled_date}</span>` : ""}
      <span class="badge bg-light text-dark border"><i class="bi bi-clock me-1"></i>${timeLabel}</span>
      ${task.notes ? `<span class="badge bg-warning text-dark" title="${escapeHtml(task.notes)}"><i class="bi bi-journal-text"></i></span>` : ""}
      <div class="action-btn-group d-flex gap-1">
        <button class="btn btn-sm btn-outline-primary py-0 px-1 edit-task-btn" title="Edit / add notes">
          <i class="bi bi-pencil" style="font-size:0.65rem"></i>
        </button>
        <button class="btn btn-sm btn-outline-danger py-0 px-1 delete-task-btn" title="Delete">
          <i class="bi bi-trash" style="font-size:0.65rem"></i>
        </button>
      </div>
    </div>
  `;

  // Toggle completion on checkbox click
  div.querySelector(".task-checkbox").addEventListener("change", async (e) => {
    try {
      await PUT(`/api/tasks/${task.id}`, { completed: e.target.checked });
      task.completed = e.target.checked;
      div.className = `task-item ${task.completed ? "completed" : ""}`;
      // Refresh progress bars in plan header
      state.currentPlan = await GET(`/api/plans/${state.currentPlan.id}`);
      updateProgressBars();
      showToast(task.completed ? "✅ Task completed!" : "Task marked incomplete");
    } catch (err) {
      showToast("Failed to update task: " + err.message, "danger");
      e.target.checked = !e.target.checked;  // Revert checkbox
    }
  });

  // Edit task on button click
  div.querySelector(".edit-task-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    openEditTaskModal(task);
  });

  // Delete task on button click
  div.querySelector(".delete-task-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    deleteTask(task.id);
  });

  return div;
}

/**
 * Update progress bars without re-rendering the whole plan.
 * This is called after toggling task completion for a smoother UX.
 */
function updateProgressBars() {
  const plan = state.currentPlan;
  const allTasks = plan.goals.flatMap(g => g.subtasks.flatMap(s => s.daily_tasks));
  const totalTasks = allTasks.length;
  const doneTasks = allTasks.filter(t => t.completed).length;
  const pct = totalTasks > 0 ? Math.round(doneTasks / totalTasks * 100) : 0;

  document.getElementById("plan-progress-bar").style.width = `${pct}%`;
  document.getElementById("plan-progress-text").textContent =
    `${doneTasks}/${totalTasks} tasks (${pct}%)`;
}


// =============================================================================
// PLAN CRUD
// =============================================================================

function openCreatePlanModal() {
  state.editingPlanId = null;
  document.getElementById("plan-modal-label").textContent = "New Learning Plan";
  document.getElementById("plan-title-input").value = "";
  document.getElementById("plan-desc-input").value = "";
  planModal.show();
}

function openEditPlanModal() {
  state.editingPlanId = state.currentPlan.id;
  document.getElementById("plan-modal-label").textContent = "Edit Plan";
  document.getElementById("plan-title-input").value = state.currentPlan.title;
  document.getElementById("plan-desc-input").value = state.currentPlan.description || "";
  planModal.show();
}

async function savePlan() {
  const title = document.getElementById("plan-title-input").value.trim();
  const description = document.getElementById("plan-desc-input").value.trim() || null;

  if (!title) {
    showToast("Plan title is required", "warning");
    return;
  }

  try {
    if (state.editingPlanId) {
      await PUT(`/api/plans/${state.editingPlanId}`, { title, description });
      showToast("Plan updated!");
    } else {
      const newPlan = await POST("/api/plans", { title, description });
      showToast("Plan created!");
      state.currentPlan = newPlan;
    }
    planModal.hide();
    await loadPlans();
    if (state.currentPlan) {
      await selectPlan(state.currentPlan.id);
    }
  } catch (e) {
    showToast("Error: " + e.message, "danger");
  }
}

async function deletePlan() {
  if (!state.currentPlan) return;
  if (!confirm(`Delete "${state.currentPlan.title}" and everything in it? This cannot be undone.`)) return;

  try {
    await DELETE(`/api/plans/${state.currentPlan.id}`);
    state.currentPlan = null;
    document.getElementById("plan-view").style.display = "none";
    document.getElementById("welcome-screen").style.display = "";
    await loadPlans();
    showToast("Plan deleted");
  } catch (e) {
    showToast("Failed to delete: " + e.message, "danger");
  }
}


// =============================================================================
// GOAL CRUD
// =============================================================================

function openCreateGoalModal() {
  state.editingGoalId = null;
  document.getElementById("goal-modal-label").textContent = "New Goal";
  document.getElementById("goal-title-input").value = "";
  document.getElementById("goal-desc-input").value = "";
  document.getElementById("goal-start-input").value = "";
  document.getElementById("goal-end-input").value = "";
  goalModal.show();
}

function openEditGoalModal(goal) {
  state.editingGoalId = goal.id;
  document.getElementById("goal-modal-label").textContent = "Edit Goal";
  document.getElementById("goal-title-input").value = goal.title;
  document.getElementById("goal-desc-input").value = goal.description || "";
  document.getElementById("goal-start-input").value = goal.start_date || "";
  document.getElementById("goal-end-input").value = goal.end_date || "";
  goalModal.show();
}

async function saveGoal() {
  const title = document.getElementById("goal-title-input").value.trim();
  const description = document.getElementById("goal-desc-input").value.trim() || null;
  const start_date = document.getElementById("goal-start-input").value || null;
  const end_date = document.getElementById("goal-end-input").value || null;

  if (!title) {
    showToast("Goal title is required", "warning");
    return;
  }

  try {
    if (state.editingGoalId) {
      await PUT(`/api/goals/${state.editingGoalId}`, { title, description, start_date, end_date });
      showToast("Goal updated!");
    } else {
      await POST(`/api/plans/${state.currentPlan.id}/goals`, { title, description, start_date, end_date });
      showToast("Goal created!");
    }
    goalModal.hide();
    await selectPlan(state.currentPlan.id);
  } catch (e) {
    showToast("Error: " + e.message, "danger");
  }
}

async function deleteGoal(goalId) {
  const goal = state.currentPlan.goals.find(g => g.id === goalId);
  if (!confirm(`Delete goal "${goal?.title}"? This will also delete all its subtasks and tasks.`)) return;

  try {
    await DELETE(`/api/goals/${goalId}`);
    showToast("Goal deleted");
    await selectPlan(state.currentPlan.id);
  } catch (e) {
    showToast("Failed to delete: " + e.message, "danger");
  }
}


// =============================================================================
// SUBTASK CRUD
// =============================================================================

function openCreateSubtaskModal(goalId) {
  state.editingSubtaskId = null;
  state.contextGoalId = goalId;
  document.getElementById("subtask-modal-label").textContent = "New Subtask";
  document.getElementById("subtask-title-input").value = "";
  document.getElementById("subtask-desc-input").value = "";
  subtaskModal.show();
}

function openEditSubtaskModal(subtask) {
  state.editingSubtaskId = subtask.id;
  document.getElementById("subtask-modal-label").textContent = "Edit Subtask";
  document.getElementById("subtask-title-input").value = subtask.title;
  document.getElementById("subtask-desc-input").value = subtask.description || "";
  subtaskModal.show();
}

async function saveSubtask() {
  const title = document.getElementById("subtask-title-input").value.trim();
  const description = document.getElementById("subtask-desc-input").value.trim() || null;

  if (!title) {
    showToast("Subtask title is required", "warning");
    return;
  }

  try {
    if (state.editingSubtaskId) {
      await PUT(`/api/subtasks/${state.editingSubtaskId}`, { title, description });
      showToast("Subtask updated!");
    } else {
      await POST(`/api/goals/${state.contextGoalId}/subtasks`, { title, description });
      showToast("Subtask created!");
    }
    subtaskModal.hide();
    await selectPlan(state.currentPlan.id);
  } catch (e) {
    showToast("Error: " + e.message, "danger");
  }
}

async function deleteSubtask(subtaskId) {
  if (!confirm("Delete this subtask and all its daily tasks?")) return;

  try {
    await DELETE(`/api/subtasks/${subtaskId}`);
    showToast("Subtask deleted");
    await selectPlan(state.currentPlan.id);
  } catch (e) {
    showToast("Failed to delete: " + e.message, "danger");
  }
}


// =============================================================================
// DAILY TASK CRUD
// =============================================================================

function openCreateTaskModal(subtaskId) {
  state.editingTaskId = null;
  state.contextSubtaskId = subtaskId;
  document.getElementById("task-modal-label").textContent = "New Daily Task";
  document.getElementById("task-title-input").value = "";
  document.getElementById("task-desc-input").value = "";
  document.getElementById("task-date-input").value = "";
  document.getElementById("task-minutes-input").value = "30";
  document.getElementById("task-notes-input").value = "";
  document.getElementById("task-notes-section").style.display = "none";
  taskModal.show();
}

function openEditTaskModal(task) {
  state.editingTaskId = task.id;
  document.getElementById("task-modal-label").textContent = "Edit Daily Task";
  document.getElementById("task-title-input").value = task.title;
  document.getElementById("task-desc-input").value = task.description || "";
  document.getElementById("task-date-input").value = task.scheduled_date || "";
  document.getElementById("task-minutes-input").value = task.estimated_minutes;
  document.getElementById("task-notes-input").value = task.notes || "";
  // Show notes section when editing (user can log their progress)
  document.getElementById("task-notes-section").style.display = "block";
  taskModal.show();
}

async function saveTask() {
  const title = document.getElementById("task-title-input").value.trim();
  const description = document.getElementById("task-desc-input").value.trim() || null;
  const scheduled_date = document.getElementById("task-date-input").value || null;
  const estimated_minutes = parseInt(document.getElementById("task-minutes-input").value) || 30;
  const notes = document.getElementById("task-notes-input").value.trim() || null;

  if (!title) {
    showToast("Task title is required", "warning");
    return;
  }

  try {
    if (state.editingTaskId) {
      await PUT(`/api/tasks/${state.editingTaskId}`, { title, description, scheduled_date, estimated_minutes, notes });
      showToast("Task updated!");
    } else {
      await POST(`/api/subtasks/${state.contextSubtaskId}/tasks`, { title, description, scheduled_date, estimated_minutes });
      showToast("Task created!");
    }
    taskModal.hide();
    await selectPlan(state.currentPlan.id);
  } catch (e) {
    showToast("Error: " + e.message, "danger");
  }
}

async function deleteTask(taskId) {
  if (!confirm("Delete this daily task?")) return;

  try {
    await DELETE(`/api/tasks/${taskId}`);
    showToast("Task deleted");
    await selectPlan(state.currentPlan.id);
  } catch (e) {
    showToast("Failed to delete: " + e.message, "danger");
  }
}


// =============================================================================
// AI GENERATION
// =============================================================================

async function openAiModal() {
  // Reset the modal
  state.aiGeneratedPlan = null;
  document.getElementById("ai-topic-input").value = "";
  document.getElementById("ai-weeks-input").value = "4";
  document.getElementById("ai-hours-input").value = "1";
  document.getElementById("ai-form-section").style.display = "block";
  document.getElementById("ai-loading").classList.add("d-none");
  document.getElementById("ai-preview").classList.add("d-none");
  document.getElementById("ai-generate-submit-btn").classList.remove("d-none");
  document.getElementById("ai-import-btn").classList.add("d-none");
  document.getElementById("ai-no-key-warning").classList.add("d-none");

  // Check if any AI provider is configured
  try {
    const status = await GET("/api/ai/status");
    if (!status.groq && !status.openai) {
      document.getElementById("ai-no-key-warning").classList.remove("d-none");
    }
  } catch (_) { /* ignore */ }

  aiModal.show();
}

async function generateWithAi() {
  const topic = document.getElementById("ai-topic-input").value.trim();
  if (!topic) {
    showToast("Please describe what you want to learn", "warning");
    return;
  }

  const duration_weeks = parseInt(document.getElementById("ai-weeks-input").value) || 4;
  const hours_per_day = parseFloat(document.getElementById("ai-hours-input").value) || 1;

  // Show loading state
  document.getElementById("ai-form-section").style.display = "none";
  document.getElementById("ai-loading").classList.remove("d-none");
  document.getElementById("ai-generate-submit-btn").classList.add("d-none");

  try {
    const plan = await POST("/api/ai/generate", { topic, duration_weeks, hours_per_day });
    state.aiGeneratedPlan = plan;

    // Show the preview
    document.getElementById("ai-loading").classList.add("d-none");
    document.getElementById("ai-preview").classList.remove("d-none");
    document.getElementById("ai-import-btn").classList.remove("d-none");

    renderAiPreview(plan);
  } catch (e) {
    document.getElementById("ai-loading").classList.add("d-none");
    document.getElementById("ai-form-section").style.display = "block";
    document.getElementById("ai-generate-submit-btn").classList.remove("d-none");
    showToast("AI generation failed: " + e.message, "danger");
  }
}

function renderAiPreview(plan) {
  const container = document.getElementById("ai-preview-content");
  let html = `<p class="fw-bold fs-6 mb-1">${escapeHtml(plan.plan_title)}</p>
    <p class="text-muted small mb-3">${escapeHtml(plan.plan_description || "")}</p>`;

  for (const goal of plan.goals) {
    html += `<p class="ai-goal-title"><i class="bi bi-bullseye me-1"></i>${escapeHtml(goal.title)}</p>`;
    if (goal.description) {
      html += `<p class="text-muted small ms-3 mb-1">${escapeHtml(goal.description)}</p>`;
    }
    for (const subtask of (goal.subtasks || [])) {
      html += `<p class="ai-subtask-title"><i class="bi bi-layers me-1 text-muted"></i>${escapeHtml(subtask.title)}</p>`;
      for (const task of (subtask.daily_tasks || [])) {
        html += `<p class="ai-task-title"><i class="bi bi-check2 me-1"></i>${escapeHtml(task.title)}</p>`;
      }
    }
  }

  container.innerHTML = html;
}

async function importAiPlan() {
  if (!state.aiGeneratedPlan) return;

  try {
    const plan = await POST("/api/ai/import", state.aiGeneratedPlan);
    aiModal.hide();
    await loadPlans();
    await selectPlan(plan.id);
    showToast("🎉 AI plan imported! Let's get learning!");
  } catch (e) {
    showToast("Import failed: " + e.message, "danger");
  }
}


// =============================================================================
// DARK/LIGHT MODE TOGGLE
// =============================================================================

function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute("data-bs-theme") === "dark";
  html.setAttribute("data-bs-theme", isDark ? "light" : "dark");
  const icon = document.querySelector("#theme-toggle i");
  icon.className = isDark ? "bi bi-moon-fill" : "bi bi-sun-fill";
  localStorage.setItem("theme", isDark ? "light" : "dark");
}

function loadSavedTheme() {
  const saved = localStorage.getItem("theme");
  if (saved) {
    document.documentElement.setAttribute("data-bs-theme", saved);
    const icon = document.querySelector("#theme-toggle i");
    icon.className = saved === "dark" ? "bi bi-sun-fill" : "bi bi-moon-fill";
  }
}


// =============================================================================
// UTILITY
// =============================================================================

/**
 * Escape HTML special characters to prevent XSS attacks.
 * Always use this when inserting user-provided text into innerHTML.
 *
 * XSS (Cross-Site Scripting): If a user stores <script>alert('hacked')</script>
 * as a task title and we insert it raw into innerHTML, that script would run!
 * escapeHtml converts < to &lt;, > to &gt;, etc., making it display as text.
 */
function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}


// =============================================================================
// INITIALIZATION — Wire everything up when the page loads
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Bootstrap components
  initBootstrapComponents();

  // Apply saved theme
  loadSavedTheme();

  // ── Event listeners ──────────────────────────────────────────────────────

  // Theme toggle
  document.getElementById("theme-toggle").addEventListener("click", toggleTheme);

  // Sidebar: New plan button
  document.getElementById("new-plan-btn").addEventListener("click", openCreatePlanModal);

  // Sidebar: AI generate button
  document.getElementById("ai-generate-btn").addEventListener("click", openAiModal);

  // Welcome screen buttons
  document.getElementById("welcome-new-plan-btn").addEventListener("click", openCreatePlanModal);
  document.getElementById("welcome-ai-btn").addEventListener("click", openAiModal);

  // Plan view buttons
  document.getElementById("edit-plan-btn").addEventListener("click", openEditPlanModal);
  document.getElementById("add-goal-btn").addEventListener("click", openCreateGoalModal);
  document.getElementById("delete-plan-btn").addEventListener("click", deletePlan);

  // Modal save buttons
  document.getElementById("save-plan-btn").addEventListener("click", savePlan);
  document.getElementById("save-goal-btn").addEventListener("click", saveGoal);
  document.getElementById("save-subtask-btn").addEventListener("click", saveSubtask);
  document.getElementById("save-task-btn").addEventListener("click", saveTask);

  // Allow pressing Enter to submit forms in modals
  ["plan-title-input", "goal-title-input", "subtask-title-input", "task-title-input"].forEach(id => {
    document.getElementById(id).addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        document.getElementById(id.replace("-input", "").replace(
          /plan|goal|subtask|task/, m => `save-${m}`
        ) + "-btn")?.click();
      }
    });
  });

  // AI modal buttons
  document.getElementById("ai-generate-submit-btn").addEventListener("click", generateWithAi);
  document.getElementById("ai-import-btn").addEventListener("click", importAiPlan);

  // ── Initial data load ────────────────────────────────────────────────────
  loadPlans();
});
