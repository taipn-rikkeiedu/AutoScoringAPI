// DOM Elements
const githubUrlInput = document.getElementById("githubUrl");
const criteriaInput = document.getElementById("criteria");
const apiServerInput = document.getElementById("apiServer");
const providerInput = document.getElementById("provider");
const apiKeyInput = document.getElementById("apiKey");
const apiBaseUrlInput = document.getElementById("apiBaseUrl");
const modelNameInput = document.getElementById("modelName");

const gradeBtn = document.getElementById("gradeBtn");
const saveConfigBtn = document.getElementById("saveConfigBtn");

const classSelect = document.getElementById("classSelect");
const sessionSelect = document.getElementById("sessionSelect");
const exerciseSelect = document.getElementById("exerciseSelect");
const uploadFileBtn = document.getElementById("uploadFileBtn");
const exerciseFileInput = document.getElementById("exerciseFile");

const graderStatus = document.getElementById("graderStatus");
const settingsStatus = document.getElementById("settingsStatus");
const reportContainer = document.getElementById("reportContainer");
const reportContent = document.getElementById("reportContent");

const serverStatusDot = document.getElementById("serverStatusDot");
const serverStatusText = document.getElementById("serverStatusText");

// Tab Elements
const tabGraderBtn = document.getElementById("tabGraderBtn");
const tabSettingsBtn = document.getElementById("tabSettingsBtn");
const tabGrader = document.getElementById("tabGrader");
const tabSettings = document.getElementById("tabSettings");

// Global API Server variable
let API_SERVER = "http://localhost:8000";

// Initialize
async function initialize() {
  // Load saved API Server from Chrome storage
  chrome.storage.local.get(["apiServerUrl"], async function (result) {
    if (result.apiServerUrl) {
      API_SERVER = result.apiServerUrl;
    }
    apiServerInput.value = API_SERVER;
    
    // Check connection after getting server url
    const isOnline = await checkServerStatus();
    if (isOnline) {
      await loadTemplates();
    }
    // Load config from Backend
    await loadBackendConfig();
  });

  // Auto-fill GitHub URL from current tab
  chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    if (tabs && tabs[0] && tabs[0].url) {
      const currentUrl = tabs[0].url;
      const githubMatch = currentUrl.match(/^https?:\/\/(www\.)?github\.com\/([^/]+)\/([^/]+)/);
      if (githubMatch) {
        githubUrlInput.value = githubMatch[0];
      }
    }
  });

  // Setup tab listeners
  tabGraderBtn.addEventListener("click", () => switchTab("grader"));
  tabSettingsBtn.addEventListener("click", () => switchTab("settings"));

  // Form submit listeners
  gradeBtn.addEventListener("click", gradeRepo);
  saveConfigBtn.addEventListener("click", saveConfig);

  // Template select and upload file listeners
  classSelect.addEventListener("change", handleClassChange);
  sessionSelect.addEventListener("change", handleSessionChange);
  exerciseSelect.addEventListener("change", handleExerciseChange);
  uploadFileBtn.addEventListener("click", () => exerciseFileInput.click());
  exerciseFileInput.addEventListener("change", uploadTemplateFile);
}

// Switch between Grader and Settings tabs
function switchTab(tabName) {
  if (tabName === "grader") {
    tabGraderBtn.classList.add("active");
    tabSettingsBtn.classList.remove("active");
    tabGrader.classList.add("active");
    tabSettings.classList.remove("active");
  } else {
    tabGraderBtn.classList.remove("active");
    tabSettingsBtn.classList.add("active");
    tabGrader.classList.remove("active");
    tabSettings.classList.add("active");
  }
}

// Ping API Server to check if Online/Offline
async function checkServerStatus() {
  serverStatusText.textContent = "Đang kết nối...";
  serverStatusDot.className = "status-dot";
  
  try {
    const response = await fetch(`${API_SERVER}/health`, { method: "GET" });
    if (response.ok) {
      const data = await response.json();
      if (data.status === "ok") {
        serverStatusDot.classList.add("online");
        serverStatusText.textContent = "Đã kết nối";
        return true;
      }
    }
  } catch (error) {
    // Fail silently
  }
  
  serverStatusDot.className = "status-dot";
  serverStatusText.textContent = "Không có kết nối";
  return false;
}

// Load configurations from Backend server
async function loadBackendConfig() {
  try {
    const response = await fetch(`${API_SERVER}/config`);
    if (response.ok) {
      const config = await response.json();
      if (config.provider) providerInput.value = config.provider;
      if (config.gemini_api_key && config.provider === "gemini") apiKeyInput.value = config.gemini_api_key;
      else if (config.deepseek_api_key && config.provider === "deepseek") apiKeyInput.value = config.deepseek_api_key;
      else if (config.openrouter_api_key && config.provider === "openrouter") apiKeyInput.value = config.openrouter_api_key;
      else if (config.custom_api_key && config.provider === "custom") apiKeyInput.value = config.custom_api_key;

      if (config.provider === "gemini" && config.gemini_model_name) modelNameInput.value = config.gemini_model_name;
      else if (config.provider === "deepseek" && config.deepseek_model_name) modelNameInput.value = config.deepseek_model_name;
      else if (config.provider === "openrouter" && config.openrouter_model_name) modelNameInput.value = config.openrouter_model_name;
      else if (config.provider === "custom" && config.custom_model_name) modelNameInput.value = config.custom_model_name;
      else if (config.provider === "local" && config.local_model_name) modelNameInput.value = config.local_model_name;

      if (config.provider === "deepseek" && config.deepseek_api_base_url) apiBaseUrlInput.value = config.deepseek_api_base_url;
      else if (config.provider === "openrouter" && config.openrouter_api_base_url) apiBaseUrlInput.value = config.openrouter_api_base_url;
      else if (config.provider === "custom" && config.custom_api_base_url) apiBaseUrlInput.value = config.custom_api_base_url;
      else if (config.provider === "local" && config.ollama_base_url) apiBaseUrlInput.value = config.ollama_base_url;
    }
  } catch (error) {
    console.error("Không thể tải cấu hình từ backend:", error);
  }
}

// Save configurations to backend and save API Server URL to local storage
async function saveConfig() {
  settingsStatus.textContent = "Đang lưu...";
  settingsStatus.style.color = "var(--text-secondary)";
  
  const serverUrl = apiServerInput.value.trim().replace(/\/$/, "");
  if (!serverUrl) {
    settingsStatus.textContent = "Vui lòng nhập URL API Server hợp lệ.";
    settingsStatus.style.color = "var(--danger)";
    return;
  }

  // Save server URL to Chrome local storage
  chrome.storage.local.set({ apiServerUrl: serverUrl }, async function () {
    API_SERVER = serverUrl;
    
    // Check server status with new URL
    const isOnline = await checkServerStatus();
    if (!isOnline) {
      settingsStatus.textContent = "Không thể kết nối đến API Server mới.";
      settingsStatus.style.color = "var(--danger)";
      return;
    }

    // Load templates from the new server
    await loadTemplates();

    // Prepare config payload
    const payload = {
      provider: providerInput.value,
    };

    const prov = providerInput.value;
    const key = apiKeyInput.value.trim();
    const base = apiBaseUrlInput.value.trim();
    const model = modelNameInput.value.trim();

    if (prov === "gemini") {
      payload.gemini_api_key = key;
      if (model) payload.gemini_model_name = model;
    } else if (prov === "deepseek") {
      payload.deepseek_api_key = key;
      if (base) payload.deepseek_api_base_url = base;
      if (model) payload.deepseek_model_name = model;
    } else if (prov === "openrouter") {
      payload.openrouter_api_key = key;
      if (base) payload.openrouter_api_base_url = base;
      if (model) payload.openrouter_model_name = model;
    } else if (prov === "custom") {
      payload.custom_api_key = key;
      if (base) payload.custom_api_base_url = base;
      if (model) payload.custom_model_name = model;
    } else if (prov === "local") {
      if (base) payload.ollama_base_url = base;
      if (model) payload.local_model_name = model;
    }

    try {
      const response = await fetch(`${API_SERVER}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        settingsStatus.textContent = "Lưu cấu hình thành công.";
        settingsStatus.style.color = "var(--success)";
        setTimeout(() => { settingsStatus.textContent = ""; }, 3000);
      } else {
        throw new Error("Ghi cấu hình thất bại.");
      }
    } catch (error) {
      settingsStatus.textContent = `Lỗi: ${error.message}`;
      settingsStatus.style.color = "var(--danger)";
    }
  });
}

// Grade GitHub project
async function gradeRepo() {
  const githubUrl = githubUrlInput.value.trim();
  const criteria = criteriaInput.value.trim();
  
  if (!githubUrl) {
    graderStatus.textContent = "Hãy điền URL GitHub.";
    graderStatus.style.color = "var(--danger)";
    return;
  }

  gradeBtn.disabled = true;
  graderStatus.textContent = "Đang phân tích và đánh giá mã nguồn...";
  graderStatus.style.color = "var(--text-secondary)";
  reportContainer.style.display = "none";

  const payload = {
    github_url: githubUrl,
  };
  
  if (criteria) {
    payload.criteria = criteria;
  }

  try {
    const response = await fetch(`${API_SERVER}/grade`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Đã xảy ra lỗi khi chấm điểm.");
    }

    graderStatus.innerHTML = `Đánh giá xong! <strong style="color: var(--success); font-size: 14px;">${data.score} điểm</strong> (${data.provider_display_name})`;
    graderStatus.style.color = "var(--text-primary)";
    
    // Parse Markdown to HTML using marked.js
    if (typeof marked !== 'undefined') {
      reportContent.innerHTML = marked.parse(data.report);
    } else {
      // Fallback text
      reportContent.textContent = data.report;
    }
    
    reportContainer.style.display = "block";
  } catch (error) {
    graderStatus.textContent = `Lỗi: ${error.message}`;
    graderStatus.style.color = "var(--danger)";
  } finally {
    gradeBtn.disabled = false;
  }
}

// Global templates cache
let templatesCache = {};

// Load templates list from API Backend
async function loadTemplates() {
  try {
    const response = await fetch(`${API_SERVER}/exercises`);
    if (response.ok) {
      templatesCache = await response.json();
      
      // Clear existing options except placeholders
      classSelect.innerHTML = '<option value="">-- Chọn Môn học / Lớp --</option>';
      sessionSelect.innerHTML = '<option value="">-- Chọn Session / Bài học --</option>';
      exerciseSelect.innerHTML = '<option value="">-- Chọn Bài tập --</option>';
      
      sessionSelect.disabled = true;
      exerciseSelect.disabled = true;
      
      // Populate class select
      for (const className in templatesCache) {
        const option = document.createElement("option");
        option.value = className;
        option.textContent = className;
        classSelect.appendChild(option);
      }
    }
  } catch (error) {
    console.error("Không thể tải danh sách đề bài mẫu:", error);
  }
}

// Handle Class select change
function handleClassChange() {
  const selectedClass = classSelect.value;
  
  // Reset session and exercise selects
  sessionSelect.innerHTML = '<option value="">-- Chọn Session / Bài học --</option>';
  exerciseSelect.innerHTML = '<option value="">-- Chọn Bài tập --</option>';
  sessionSelect.disabled = true;
  exerciseSelect.disabled = true;
  criteriaInput.value = "";
  
  if (selectedClass && templatesCache[selectedClass]) {
    const sessions = templatesCache[selectedClass];
    for (const sessionName in sessions) {
      const option = document.createElement("option");
      option.value = sessionName;
      option.textContent = sessionName;
      sessionSelect.appendChild(option);
    }
    sessionSelect.disabled = false;
  }
}

// Handle Session select change
function handleSessionChange() {
  const selectedClass = classSelect.value;
  const selectedSession = sessionSelect.value;
  
  // Reset exercise select
  exerciseSelect.innerHTML = '<option value="">-- Chọn Bài tập --</option>';
  exerciseSelect.disabled = true;
  criteriaInput.value = "";
  
  if (selectedClass && selectedSession && templatesCache[selectedClass][selectedSession]) {
    const exercises = templatesCache[selectedClass][selectedSession];
    for (const exerciseName in exercises) {
      const option = document.createElement("option");
      option.value = exerciseName;
      option.textContent = exerciseName;
      exerciseSelect.appendChild(option);
    }
    exerciseSelect.disabled = false;
  }
}

// Handle Exercise select change
function handleExerciseChange() {
  const selectedClass = classSelect.value;
  const selectedSession = sessionSelect.value;
  const selectedExercise = exerciseSelect.value;
  
  if (selectedClass && selectedSession && selectedExercise && templatesCache[selectedClass][selectedSession][selectedExercise]) {
    const ex = templatesCache[selectedClass][selectedSession][selectedExercise];
    
    // Concatenate assignment and criteria into the textarea
    criteriaInput.value = `ĐỀ BÀI:\n${ex.assignment || ""}\n\nTIÊU CHÍ CHẤM ĐIỂM:\n${ex.criteria || ""}`;
  } else {
    criteriaInput.value = "";
  }
}

// Upload local file and populate criteria
async function uploadTemplateFile(event) {
  const file = event.target.files[0];
  if (!file) return;

  graderStatus.textContent = "Đang đọc tệp tin...";
  graderStatus.style.color = "var(--text-secondary)";

  const fileName = file.name.toLowerCase();
  
  if (fileName.endsWith(".txt") || fileName.endsWith(".md")) {
    const reader = new FileReader();
    reader.onload = function (e) {
      criteriaInput.value = e.target.result;
      graderStatus.textContent = `Đã tải đề bài từ file: ${file.name}`;
      graderStatus.style.color = "var(--success)";
      setTimeout(() => { graderStatus.textContent = ""; }, 3000);
    };
    reader.onerror = function () {
      graderStatus.textContent = "Không thể đọc tệp tin văn bản.";
      graderStatus.style.color = "var(--danger)";
    };
    reader.readAsText(file);
  } else if (fileName.endsWith(".docx")) {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_SERVER}/parse-docx`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        if (data.text) {
          criteriaInput.value = data.text;
          graderStatus.textContent = `Đã phân tích và tải đề bài từ file docx: ${file.name}`;
          graderStatus.style.color = "var(--success)";
          setTimeout(() => { graderStatus.textContent = ""; }, 3000);
        } else {
          throw new Error("Không thể trích xuất văn bản từ docx.");
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Lỗi khi gửi tệp lên server.");
      }
    } catch (error) {
      graderStatus.textContent = `Lỗi đọc docx: ${error.message}`;
      graderStatus.style.color = "var(--danger)";
    }
  } else {
    graderStatus.textContent = "Chỉ hỗ trợ tệp tin định dạng .txt, .md, .docx";
    graderStatus.style.color = "var(--danger)";
  }

  // Clear input value so same file can be selected again
  exerciseFileInput.value = "";
}

// Run initial configurations
document.addEventListener("DOMContentLoaded", initialize);
