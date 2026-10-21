(()=>{
  'use strict';
  const body=document.body;
  const lesson=body.dataset.lesson;
  const lessonName=body.dataset.lessonName||lesson;
  const practiceKey=`ncloud-learning-${lesson}-practice`;
  const progressKey=`ncloud-learning-${lesson}-progress`;
  const quizIds=[...document.querySelectorAll('[data-quiz]')].map(quiz=>quiz.dataset.quiz);
  let solved={};
  function safeSet(key,value){
    try{localStorage.setItem(key,value);return true;}catch(_){return false;}
  }
  try{solved=JSON.parse(localStorage.getItem(practiceKey)||'{}');}catch(_){solved={};}

  document.querySelectorAll('[data-quiz]').forEach(quiz=>{
    const quizId=quiz.dataset.quiz;
    const correct=quiz.dataset.correct;
    const feedback=quiz.querySelector('[data-feedback]');
    const status=quiz.querySelector('[data-quiz-status]');
    const buttons=[...quiz.querySelectorAll('[data-choice]')];
    function showSolved(){
      if(!solved[quizId])return;
      buttons.forEach(button=>button.classList.toggle('correct',button.dataset.choice===correct));
      feedback.hidden=false;
      feedback.innerHTML=`<strong>已完成。</strong> ${quiz.dataset.explain}`;
      if(status)status.textContent='已答對';
    }
    buttons.forEach(button=>button.addEventListener('click',()=>{
      const matched=button.dataset.choice===correct;
      buttons.forEach(item=>{
        item.classList.toggle('correct',item.dataset.choice===correct);
        item.classList.toggle('not-first',!matched&&item===button);
      });
      feedback.hidden=false;
      feedback.innerHTML=`<strong>${matched?'判斷正確。':'再看一次證據。'}</strong> ${matched?quiz.dataset.explain:quiz.dataset.hint}`;
      if(matched){
        solved[quizId]=true;
        const stored=safeSet(practiceKey,JSON.stringify(solved));
        if(!stored)feedback.append('（瀏覽器未允許保存，但本次作答仍有效。）');
        if(status)status.textContent='已答對';
      }else if(status){status.textContent='尚未答對';}
    }));
    showSolved();
  });

  const boxes=[...document.querySelectorAll('[data-progress]')];
  let saved={};
  try{saved=JSON.parse(localStorage.getItem(progressKey)||'{}');}catch(_){saved={};}
  boxes.forEach(box=>{
    box.checked=Boolean(saved[box.dataset.progress]);
    box.addEventListener('change',saveProgress);
  });
  function saveProgress(){
    const state=Object.fromEntries(boxes.map(box=>[box.dataset.progress,box.checked]));
    safeSet(progressKey,JSON.stringify(state));
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
    if(done===boxes.length&&practicesDone===quizIds.length){
      const stored=safeSet(`${progressKey}-complete`,'true');
      message.textContent=`${lessonName}完成。${stored?'你的學習紀錄已保存在這個瀏覽器。':'本次已完成，但瀏覽器未允許保存進度。'}`;
    }else{
      const missing=[];
      if(practicesDone<quizIds.length)missing.push(`${quizIds.length-practicesDone} 題實作`);
      if(done<boxes.length)missing.push(`${boxes.length-done} 項自評`);
      message.textContent=`還有 ${missing.join('、')}尚未完成；請回到對應段落再試一次。`;
    }
  });
})();
