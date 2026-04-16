(function () {
  const canvas = document.getElementById("scene-canvas");
  if (!canvas) return;

  const data = window.sceneEditorData || { avatars: [], backgrounds: [] };
  const addAvatarBtn = document.getElementById("add-avatar-btn");
  const addTextBtn = document.getElementById("add-text-btn");
  const form = document.getElementById("scene-form");
  const objectsField = document.getElementById("objects-json");
  const textsField = document.getElementById("texts-json");
  const optionsField = document.getElementById("options-json");
  const answerMode = document.getElementById("scene-answer-mode");
  const choicesEditor = document.getElementById("choices-editor");
  const choicesList = document.getElementById("choices-list");
  const addChoiceBtn = document.getElementById("add-choice-btn");
  const bgSelect = document.getElementById("scene-background");

  const state = {
    objects: [],
    texts: [],
    options: [],
  };

  const setCanvasBackground = () => {
    const selectedId = bgSelect?.value;
    const bg = data.backgrounds.find((x) => String(x.id) === String(selectedId));
    if (bg && bg.image) {
      canvas.style.backgroundImage = `url(${bg.image})`;
      canvas.style.backgroundSize = "cover";
      canvas.style.backgroundPosition = "center";
    } else {
      canvas.style.backgroundImage = "none";
      canvas.style.backgroundColor = "#eef3ff";
    }
  };

  const makeDraggable = (el, target) => {
    let dragging = false;
    let startX = 0;
    let startY = 0;
    el.addEventListener("mousedown", (e) => {
      dragging = true;
      startX = e.clientX - target.x;
      startY = e.clientY - target.y;
    });
    document.addEventListener("mousemove", (e) => {
      if (!dragging) return;
      target.x = e.clientX - startX;
      target.y = e.clientY - startY;
      el.style.left = `${target.x}px`;
      el.style.top = `${target.y}px`;
    });
    document.addEventListener("mouseup", () => {
      dragging = false;
    });
  };

  const render = () => {
    canvas.innerHTML = "";
    state.objects.forEach((obj) => {
      const el = document.createElement("div");
      el.className = "scene-object";
      el.style.left = `${obj.x}px`;
      el.style.top = `${obj.y}px`;
      el.style.width = `${obj.width}px`;
      el.style.height = `${obj.height}px`;
      el.style.transform = `scale(${obj.flip_x ? -obj.scale : obj.scale}, ${obj.scale})`;
      el.style.zIndex = String(obj.z_index || 1);
      const img = document.createElement("img");
      img.src = obj.preview || "";
      el.appendChild(img);
      makeDraggable(el, obj);
      canvas.appendChild(el);
    });

    state.texts.forEach((txt) => {
      const el = document.createElement("div");
      el.className = "scene-object scene-text";
      el.style.left = `${txt.x}px`;
      el.style.top = `${txt.y}px`;
      el.style.width = `${txt.width}px`;
      el.style.fontSize = `${txt.font_size}px`;
      el.textContent = txt.text;
      makeDraggable(el, txt);
      canvas.appendChild(el);
    });
  };

  const addChoice = (row) => {
    const item = row || { option_text: "", is_correct: false, score: 0 };
    state.options.push(item);
    drawChoices();
  };

  const drawChoices = () => {
    if (!choicesList) return;
    choicesList.innerHTML = "";
    state.options.forEach((opt, idx) => {
      const wrap = document.createElement("div");
      wrap.style.display = "grid";
      wrap.style.gridTemplateColumns = "1fr auto auto auto";
      wrap.style.gap = "8px";
      const text = document.createElement("input");
      text.value = opt.option_text;
      text.oninput = () => (opt.option_text = text.value);
      const correct = document.createElement("input");
      correct.type = "checkbox";
      correct.checked = !!opt.is_correct;
      correct.onchange = () => (opt.is_correct = correct.checked);
      const score = document.createElement("input");
      score.type = "number";
      score.value = String(opt.score || 0);
      score.style.width = "90px";
      score.oninput = () => (opt.score = parseInt(score.value || "0", 10) || 0);
      const del = document.createElement("button");
      del.type = "button";
      del.className = "btn";
      del.style.background = "#8b1e1e";
      del.textContent = "Удалить";
      del.onclick = () => {
        state.options.splice(idx, 1);
        drawChoices();
      };
      wrap.appendChild(text);
      wrap.appendChild(correct);
      wrap.appendChild(score);
      wrap.appendChild(del);
      choicesList.appendChild(wrap);
    });
  };

  addAvatarBtn?.addEventListener("click", () => {
    if (!data.avatars.length) return;
    const selected = data.avatars[0];
    state.objects.push({
      name: selected.name,
      avatar_id: selected.id,
      x: 120,
      y: 120,
      width: 180,
      height: 180,
      scale: 1,
      flip_x: false,
      z_index: state.objects.length + 1,
      preview: selected.body || selected.hair || selected.eyes || selected.clothes || selected.accessory || "",
    });
    render();
  });

  addTextBtn?.addEventListener("click", () => {
    state.texts.push({ text: "Текст", x: 100, y: 100, width: 220, font_size: 18 });
    render();
  });

  answerMode?.addEventListener("change", () => {
    choicesEditor.style.display = answerMode.value === "choices" ? "block" : "none";
  });
  addChoiceBtn?.addEventListener("click", () => addChoice());

  bgSelect?.addEventListener("change", setCanvasBackground);

  document.querySelectorAll(".load-scene-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const scene = JSON.parse(btn.dataset.scene || "{}");
      document.getElementById("scene-id").value = scene.id || "";
      document.getElementById("scene-title").value = scene.title || "";
      document.getElementById("scene-order").value = scene.order || 1;
      document.getElementById("scene-question").value = scene.question_text || "";
      document.getElementById("scene-answer-mode").value = scene.answer_mode || "open";
      document.getElementById("scene-background").value = scene.background_id || "";
      state.objects = scene.objects || [];
      state.texts = scene.texts || [];
      state.options = scene.options || [];
      render();
      drawChoices();
      setCanvasBackground();
      choicesEditor.style.display = answerMode.value === "choices" ? "block" : "none";
    });
  });

  form?.addEventListener("submit", () => {
    objectsField.value = JSON.stringify(
      state.objects.map((o) => ({
        name: o.name,
        avatar_id: o.avatar_id,
        x: o.x,
        y: o.y,
        width: o.width,
        height: o.height,
        scale: o.scale,
        flip_x: !!o.flip_x,
        z_index: o.z_index || 1,
      }))
    );
    textsField.value = JSON.stringify(state.texts);
    optionsField.value = JSON.stringify(state.options);
  });

  drawChoices();
  render();
  setCanvasBackground();
  choicesEditor.style.display = answerMode?.value === "choices" ? "block" : "none";
})();
