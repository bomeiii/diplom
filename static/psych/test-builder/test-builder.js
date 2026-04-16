(function () {
  const form = document.getElementById("test-builder-form");
  if (!form) return;

  const payloadField = document.getElementById("test-builder-payload");
  const container = document.getElementById("questions-container");
  const addTop = document.getElementById("add-question-btn");
  const addBottom = document.getElementById("add-question-bottom-btn");

  const data = Array.isArray(window.initialTestBuilderData) ? window.initialTestBuilderData : [];

  const render = () => {
    container.innerHTML = "";
    data.forEach((q, index) => {
      q.order = index + 1;
      const card = document.createElement("div");
      card.className = "tb-question-card";

      const header = document.createElement("div");
      header.className = "tb-question-header";
      const left = document.createElement("div");
      left.innerHTML = `<span class="badge">${index + 1}</span>`;
      const typeSelect = document.createElement("select");
      ["single", "multi", "open"].forEach((t) => {
        const opt = document.createElement("option");
        opt.value = t;
        opt.textContent = t === "single" ? "Один вариант" : t === "multi" ? "Несколько" : "Открытый";
        if (q.question_type === t) opt.selected = true;
        typeSelect.appendChild(opt);
      });
      typeSelect.onchange = () => {
        q.question_type = typeSelect.value;
        render();
      };
      left.appendChild(typeSelect);

      const right = document.createElement("div");
      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "btn";
      delBtn.style.background = "#8b1e1e";
      delBtn.textContent = "Удалить";
      delBtn.onclick = () => {
        data.splice(index, 1);
        render();
      };
      right.appendChild(delBtn);

      header.appendChild(left);
      header.appendChild(right);
      card.appendChild(header);

      const main = document.createElement("div");
      main.className = "tb-question-main";
      const qInput = document.createElement("input");
      qInput.type = "text";
      qInput.placeholder = "Текст вопроса";
      qInput.value = q.question_text || "";
      qInput.oninput = () => (q.question_text = qInput.value);
      main.appendChild(qInput);

      const helpInput = document.createElement("input");
      helpInput.type = "text";
      helpInput.placeholder = "Пояснение (необязательно)";
      helpInput.value = q.help_text || "";
      helpInput.oninput = () => (q.help_text = helpInput.value);
      main.appendChild(helpInput);

      const toggles = document.createElement("div");
      toggles.style.display = "flex";
      toggles.style.gap = "12px";
      const requiredLabel = document.createElement("label");
      const required = document.createElement("input");
      required.type = "checkbox";
      required.checked = q.is_required !== false;
      required.onchange = () => (q.is_required = required.checked);
      requiredLabel.appendChild(required);
      requiredLabel.append(" Обязательный");
      toggles.appendChild(requiredLabel);

      const shuffleLabel = document.createElement("label");
      const shuffle = document.createElement("input");
      shuffle.type = "checkbox";
      shuffle.checked = !!q.shuffle_options;
      shuffle.onchange = () => (q.shuffle_options = shuffle.checked);
      shuffleLabel.appendChild(shuffle);
      shuffleLabel.append(" Перемешивать варианты");
      toggles.appendChild(shuffleLabel);
      main.appendChild(toggles);

      if (q.question_type !== "open") {
        const optBlock = document.createElement("div");
        const title = document.createElement("div");
        title.textContent = "Варианты ответа";
        optBlock.appendChild(title);
        const hint = document.createElement("div");
        hint.className = "muted";
        hint.style.marginTop = "4px";
        hint.textContent = "Отметьте правильные варианты. Баллы — вес правильных вариантов (учитываются только если ответ выбран правильно).";
        optBlock.appendChild(hint);
        const list = document.createElement("div");
        list.className = "tb-options-list";
        q.options = Array.isArray(q.options) ? q.options : [];
        if (!q.options.length) {
          q.options.push({ option_text: "", is_correct: false, score: 0 });
        }
        q.options.forEach((o, oIndex) => {
          o.order = oIndex + 1;
          const row = document.createElement("div");
          row.className = "tb-option-row";
          const txt = document.createElement("input");
          txt.type = "text";
          txt.value = o.option_text || "";
          txt.placeholder = "Вариант";
          txt.oninput = () => (o.option_text = txt.value);
          const correctLabel = document.createElement("label");
          correctLabel.className = "tb-flag";
          const correct = document.createElement("input");
          correct.type = "checkbox";
          correct.checked = !!o.is_correct;
          correct.onchange = () => (o.is_correct = correct.checked);
          correctLabel.appendChild(correct);
          correctLabel.append(" Правильный");
          const score = document.createElement("input");
          score.type = "number";
          score.className = "tb-small";
          score.value = String(o.score || 0);
          score.oninput = () => (o.score = parseInt(score.value || "0", 10) || 0);
          score.title = "Баллы за правильный вариант";
          const del = document.createElement("button");
          del.type = "button";
          del.className = "btn";
          del.style.background = "#8b1e1e";
          del.textContent = "×";
          del.onclick = () => {
            q.options.splice(oIndex, 1);
            render();
          };
          row.appendChild(txt);
          row.appendChild(correctLabel);
          row.appendChild(score);
          row.appendChild(del);
          list.appendChild(row);
        });
        const addOpt = document.createElement("button");
        addOpt.type = "button";
        addOpt.className = "btn";
        addOpt.textContent = "+ Добавить вариант";
        addOpt.onclick = () => {
          q.options.push({ option_text: "", is_correct: false, score: 0 });
          render();
        };
        optBlock.appendChild(list);
        optBlock.appendChild(addOpt);
        main.appendChild(optBlock);
      }

      card.appendChild(main);
      container.appendChild(card);
    });
  };

  const addQuestion = () => {
    data.push({
      id: null,
      question_text: "",
      help_text: "",
      question_type: "single",
      is_required: true,
      shuffle_options: false,
      answers_view: "tile",
      options: [],
    });
    render();
  };

  addTop.onclick = addQuestion;
  addBottom.onclick = addQuestion;

  form.addEventListener("submit", () => {
    payloadField.value = JSON.stringify(data);
  });

  render();
})();

