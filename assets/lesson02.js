(()=>{
  'use strict';

  const storageKey='ncloud-learning-lesson02-progress';
  const stages=[
    {id:'produce',label:'產生',detail:'設備或服務建立原始資料'},
    {id:'send',label:'傳送',detail:'經網路送往接收端'},
    {id:'receive',label:'接收',detail:'Receiver／Collector 收到資料'},
    {id:'parse',label:'解析',detail:'辨識並正規化欄位'},
    {id:'store',label:'儲存',detail:'保存並建立可搜尋索引'},
    {id:'use',label:'使用',detail:'搜尋、圖表與告警'}
  ];
  const shuffled=['parse','produce','use','receive','store','send'];
  const bank=document.querySelector('.order-bank');
  const result=document.querySelector('.order-result ol');
  const orderStatus=document.querySelector('[data-order-status]');
  let nextIndex=0;

  function renderOrder(){
    result.replaceChildren(...stages.slice(0,nextIndex).map((stage,index)=>{
      const item=document.createElement('li');
      item.innerHTML=`<b>${String(index+1).padStart(2,'0')} · ${stage.label}</b><span>${stage.detail}</span>`;
      return item;
    }));
    bank.replaceChildren(...shuffled.map(id=>{
      const stage=stages.find(item=>item.id===id);
      const button=document.createElement('button');
      button.type='button';
      button.className='order-choice';
      button.dataset.stage=id;
      button.textContent=stage.label;
      button.disabled=stages.slice(0,nextIndex).some(item=>item.id===id);
      button.addEventListener('click',()=>chooseStage(stage,button));
      return button;
    }));
    orderStatus.textContent=nextIndex===stages.length?'排序完成！你已走完一筆資料的旅程。':`已完成 ${nextIndex} / ${stages.length}`;
    orderStatus.classList.toggle('complete',nextIndex===stages.length);
  }

  function chooseStage(stage,button){
    const expected=stages[nextIndex];
    bank.querySelectorAll('.order-choice').forEach(item=>item.classList.remove('wrong'));
    if(stage.id!==expected.id){
      button.classList.add('wrong');
      orderStatus.textContent=`再想一下：資料要先「${expected.label}」，才會走到後面的階段。`;
      return;
    }
    nextIndex+=1;
    renderOrder();
  }

  document.querySelector('[data-order-reset]').addEventListener('click',()=>{nextIndex=0;renderOrder();});
  renderOrder();

  const cases={
    missing:{
      question:'設備顯示已啟用資料傳送，但 Receiver 完全看不到新資料。第一步優先檢查哪裡？',
      answer:'來源與傳輸',
      explain:'先確認目的位址、Port、協定及網路路徑。Receiver 沒收到資料時，解析與 Dashboard 還不是第一個檢查點。'
    },
    unparsed:{
      question:'Receiver 已看到原始紀錄，但時間、來源 IP 與動作都無法分欄查詢。第一步優先檢查哪裡？',
      answer:'解析正規化',
      explain:'資料已成功抵達，問題較可能在格式辨識或欄位對應。先確認 Parser 是否辨識這種資料格式。'
    },
    dashboard:{
      question:'搜尋能找到資料，但同一時間範圍的 Dashboard 圖表是空白。第一步優先檢查哪裡？',
      answer:'圖表條件',
      explain:'既然搜尋已能找到，接收、解析與儲存大致可用。先比較 Dashboard 的時間、篩選、指標與維度。'
    }
  };
  const diagnoseChoices=['來源與傳輸','解析正規化','儲存索引','圖表條件'];
  const question=document.querySelector('#diagnose-question');
  const grid=document.querySelector('#diagnose-grid');
  const feedback=document.querySelector('#diagnose-feedback');
  let currentCase='missing';

  function renderCase(){
    const item=cases[currentCase];
    question.textContent=item.question;
    feedback.hidden=true;
    feedback.textContent='';
    grid.replaceChildren(...diagnoseChoices.map(name=>{
      const button=document.createElement('button');
      button.type='button';
      button.className='choice';
      button.textContent=name;
      button.addEventListener('click',()=>{
        grid.querySelectorAll('.choice').forEach(choice=>{
          choice.classList.toggle('correct',choice.textContent===item.answer);
          choice.classList.toggle('not-first',choice.textContent!==item.answer);
        });
        const matched=name===item.answer;
        feedback.innerHTML=`<strong>${matched?'方向正確。':`先查「${item.answer}」會更直接。`}</strong> ${item.explain}`;
        feedback.hidden=false;
      });
      return button;
    }));
  }

  document.querySelectorAll('[data-case]').forEach(tab=>tab.addEventListener('click',()=>{
    currentCase=tab.dataset.case;
    document.querySelectorAll('[data-case]').forEach(item=>{
      const active=item===tab;
      item.classList.toggle('active',active);
      item.setAttribute('aria-selected',String(active));
    });
    renderCase();
  }));
  renderCase();

  const boxes=[...document.querySelectorAll('[data-progress]')];
  let saved={};
  try{saved=JSON.parse(localStorage.getItem(storageKey)||'{}');}catch(_){saved={};}
  boxes.forEach(box=>{
    box.checked=Boolean(saved[box.dataset.progress]);
    box.addEventListener('change',saveProgress);
  });

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
      message.textContent='第二課完成。你已經能沿著資料旅程找第一個檢查點。';
    }else{
      message.textContent=`還有 ${boxes.length-done} 項尚未勾選；先回到不確定的段落再試一次。`;
    }
  });
})();
