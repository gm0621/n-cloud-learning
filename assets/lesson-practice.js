(()=>{
  'use strict';
  const body=document.body;
  const lesson=body.dataset.lesson;
  const lessonName=body.dataset.lessonName||lesson;
  const practiceKey=`ncloud-learning-${lesson}-practice`;
  const progressKey=`ncloud-learning-${lesson}-progress`;
  let solved={};
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
        localStorage.setItem(practiceKey,JSON.stringify(solved));
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
    localStorage.setItem(progressKey,JSON.stringify(state));
    updateProgress();
  }
  function updateProgress(){
    const done=boxes.filter(box=>box.checked).length;
    const bar=document.querySelector('#progress-bar');
    const text=document.querySelector('#progress-text');
    if(bar)bar.style.width=`${boxes.length?done/boxes.length*100:0}%`;
    if(text)text.textContent=`${done} / ${boxes.length}`;
  }
  updateProgress();

  const finish=document.querySelector('#finish-button');
  if(finish)finish.addEventListener('click',()=>{
    const done=boxes.filter(box=>box.checked).length;
    const message=document.querySelector('#completion-message');
    if(done===boxes.length){
      localStorage.setItem(`${progressKey}-complete`,'true');
      message.textContent=`${lessonName}完成。你的學習紀錄已保存在這個瀏覽器。`;
    }else{
      message.textContent=`還有 ${boxes.length-done} 項尚未勾選；先回到不確定的段落再試一次。`;
    }
  });
})();
