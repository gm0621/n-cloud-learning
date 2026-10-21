(()=>{
  'use strict';
  const lesson=document.body.dataset.lesson;
  const storageKey=`ncloud-learning-${lesson}-progress`;
  const scenarios={
    bandwidth:{question:'你會先看哪一種資料，找出誰占用了頻寬？',answer:'Flow',explain:'先看 Flow，因為它最適合找出來源、目的與傳輸量。找到主要流量來源後，再用 SNMP 確認設備介面是否接近滿載。'},
    login:{question:'你會先看哪一種資料，確認帳號反覆登入失敗？',answer:'Syslog',explain:'先看 Syslog，因為登入成功／失敗屬於設備或服務記錄的事件。接著可比對來源 IP、時間與失敗次數。'},
    service:{question:'網站可以開啟，但使用者說速度很慢。你會先用哪種資料確認實際回應時間？',answer:'PM',explain:'先用 PM 確認服務回應時間是否真的變差，再搭配 Flow 與 SNMP 判斷是流量、設備或服務本身造成。'}
  };
  const choices=['Syslog','Flow','SNMP','PM'];
  const question=document.querySelector('#scenario-question');
  const grid=document.querySelector('#choice-grid');
  const feedback=document.querySelector('#feedback');
  let current='bandwidth';

  function renderScenario(){
    const item=scenarios[current];
    question.textContent=item.question;
    feedback.hidden=true;
    feedback.textContent='';
    grid.replaceChildren(...choices.map(name=>{
      const button=document.createElement('button');
      button.type='button';button.className='choice';button.textContent=name;
      button.addEventListener('click',()=>{
        grid.querySelectorAll('.choice').forEach(el=>{
          el.classList.toggle('correct',el.textContent===item.answer);
          el.classList.toggle('not-first',el.textContent!==item.answer);
        });
        const matched=name===item.answer;
        feedback.innerHTML=`<strong>${matched?'方向正確。':'先從 '+item.answer+' 開始會更直接。'}</strong> ${item.explain}`;
        feedback.hidden=false;
      });
      return button;
    }));
  }
  document.querySelectorAll('.scenario-tab').forEach(tab=>tab.addEventListener('click',()=>{
    current=tab.dataset.scenario;
    document.querySelectorAll('.scenario-tab').forEach(el=>{
      const active=el===tab;el.classList.toggle('active',active);el.setAttribute('aria-selected',String(active));
    });
    renderScenario();
  }));
  renderScenario();

  const boxes=[...document.querySelectorAll('[data-progress]')];
  let saved={};
  try{saved=JSON.parse(localStorage.getItem(storageKey)||'{}')}catch(_){saved={}}
  boxes.forEach(box=>{box.checked=Boolean(saved[box.dataset.progress]);box.addEventListener('change',saveProgress)});
  function saveProgress(){
    const state=Object.fromEntries(boxes.map(box=>[box.dataset.progress,box.checked]));
    localStorage.setItem(storageKey,JSON.stringify(state));
    updateProgress();
  }
  function updateProgress(){
    const done=boxes.filter(box=>box.checked).length;
    document.querySelector('#progress-bar').style.width=`${done/boxes.length*100}%`;
    document.querySelector('#progress-text').textContent=`${done} / ${boxes.length}`;
  }
  updateProgress();
  document.querySelector('#finish-button').addEventListener('click',()=>{
    const done=boxes.filter(box=>box.checked).length;
    const message=document.querySelector('#completion-message');
    if(done===boxes.length){
      localStorage.setItem(`${storageKey}-complete`,'true');
      message.textContent='第一課完成。你的進度已保存在這個瀏覽器。';
    }else{
      message.textContent=`還有 ${boxes.length-done} 項尚未勾選；不必趕，理解後再完成。`;
    }
  });
})();
