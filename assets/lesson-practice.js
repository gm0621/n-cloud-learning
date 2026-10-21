(()=>{
  'use strict';
  const body=document.body;
  const lesson=body.dataset.lesson;
  const lessonName=body.dataset.lessonName||lesson;
  const practiceKey=`ncloud-learning-${lesson}-practice`;
  const progressKey=`ncloud-learning-${lesson}-progress`;
  const quizIds=[...document.querySelectorAll('[data-quiz]')].map(quiz=>quiz.dataset.quiz);

  function isPlainObject(value){
    return Boolean(value)&&typeof value==='object'&&!Array.isArray(value);
  }
  function readObject(key){
    try{
      const parsed=JSON.parse(localStorage.getItem(key)||'{}');
      return isPlainObject(parsed)?parsed:{};
    }catch(_){
      return {};
    }
  }
  function safeSet(key,value){
    try{localStorage.setItem(key,value);return true;}catch(_){return false;}
  }
  function renderFeedback(feedback,label,detail){
    if(!feedback)return;
    const strong=document.createElement('strong');
    strong.textContent=label;
    feedback.replaceChildren(strong,document.createTextNode(` ${detail}`));
    feedback.hidden=false;
  }
  function showStorageWarning(){
    if(document.querySelector('[data-storage-warning]'))return;
    const warning=document.createElement('p');
    warning.className='storage-warning';
    warning.dataset.storageWarning='true';
    warning.setAttribute('role','status');
    warning.textContent='瀏覽器未允許保存進度，但本次操作仍有效。';
    const anchor=document.querySelector('.progress-row')||document.querySelector('#finish-button');
    if(anchor)anchor.insertAdjacentElement('afterend',warning);
  }

  let solved=readObject(practiceKey);
  document.querySelectorAll('[data-quiz]').forEach(quiz=>{
    const quizId=quiz.dataset.quiz;
    const correct=quiz.dataset.correct;
    const feedback=quiz.querySelector('[data-feedback]');
    const status=quiz.querySelector('[data-quiz-status]');
    const buttons=[...quiz.querySelectorAll('[data-choice]')];
    if(feedback){
      feedback.setAttribute('role','status');
      feedback.setAttribute('aria-live','polite');
    }
    buttons.forEach(button=>button.setAttribute('aria-pressed','false'));
    function showSolved(){
      if(!solved[quizId])return;
      buttons.forEach(button=>{
        const matched=button.dataset.choice===correct;
        button.classList.toggle('correct',matched);
        button.setAttribute('aria-pressed',String(matched));
      });
      renderFeedback(feedback,'已完成。',quiz.dataset.explain);
      if(status)status.textContent='已答對';
    }
    buttons.forEach(button=>button.addEventListener('click',()=>{
      const matched=button.dataset.choice===correct;
      buttons.forEach(item=>{
        const selected=item===button;
        item.classList.toggle('correct',matched&&item.dataset.choice===correct);
        item.classList.toggle('not-first',!matched&&selected);
        item.setAttribute('aria-pressed',String(selected));
      });
      renderFeedback(feedback,matched?'判斷正確。':'再看一次證據。',matched?quiz.dataset.explain:quiz.dataset.hint);
      if(matched){
        solved[quizId]=true;
        if(!safeSet(practiceKey,JSON.stringify(solved))){
          if(feedback)feedback.append('（瀏覽器未允許保存，但本次作答仍有效。）');
          showStorageWarning();
        }
        if(status)status.textContent='已答對';
      }else if(status){
        status.textContent='尚未答對';
      }
    }));
    showSolved();
  });

  const boxes=[...document.querySelectorAll('[data-progress]')];
  let saved=readObject(progressKey);
  boxes.forEach(box=>{
    box.checked=Boolean(saved[box.dataset.progress]);
    box.addEventListener('change',saveProgress);
  });
  function saveProgress(){
    const state=Object.fromEntries(boxes.map(box=>[box.dataset.progress,box.checked]));
    if(!safeSet(progressKey,JSON.stringify(state)))showStorageWarning();
    updateProgress();
  }
  function updateProgress(){
    const done=boxes.filter(box=>box.checked).length;
    const bar=document.querySelector('#progress-bar');
    const text=document.querySelector('#progress-text');
    if(bar){
      const percentage=boxes.length?done/boxes.length*100:0;
      bar.style.width=`${percentage}%`;
      const track=bar.parentElement;
      if(track){
        track.setAttribute('role','progressbar');
        track.setAttribute('aria-label','本課自評進度');
        track.setAttribute('aria-valuemin','0');
        track.setAttribute('aria-valuemax',String(boxes.length));
        track.setAttribute('aria-valuenow',String(done));
      }
    }
    if(text)text.textContent=`${done} / ${boxes.length}`;
  }
  updateProgress();

  const finish=document.querySelector('#finish-button');
  if(finish)finish.addEventListener('click',()=>{
    const done=boxes.filter(box=>box.checked).length;
    const practicesDone=quizIds.filter(id=>solved[id]).length;
    const message=document.querySelector('#completion-message');
    if(!message)return;
    if(done===boxes.length&&practicesDone===quizIds.length){
      const stored=safeSet(`${progressKey}-complete`,'true');
      message.textContent=`${lessonName}完成。${stored?'你的學習紀錄已保存在這個瀏覽器。':'本次已完成，但瀏覽器未允許保存進度。'}`;
      if(!stored)showStorageWarning();
    }else{
      const missing=[];
      if(practicesDone<quizIds.length)missing.push(`${quizIds.length-practicesDone} 題實作`);
      if(done<boxes.length)missing.push(`${boxes.length-done} 項自評`);
      message.textContent=`還有 ${missing.join('、')}尚未完成；請回到對應段落再試一次。`;
    }
  });
})();
