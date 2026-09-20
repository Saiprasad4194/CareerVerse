const cards=document.querySelectorAll(".feature-card,.step-card,.testimonial-card,.roadmap-card");

const observer=new IntersectionObserver(entries=>{

entries.forEach(entry=>{

if(entry.isIntersecting){

entry.target.classList.add("show");

}

});

});

cards.forEach(card=>observer.observe(card));