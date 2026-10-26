function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("show");
}

document.addEventListener("click", function (event) {
    const sidebar = document.getElementById("sidebar");
    const button = document.querySelector(".nav-btn");
    if (!sidebar.contains(event.target) && !button.contains(event.target)) {
        sidebar.classList.remove("show");
    }
});

// Interview Analysis
const ctx=document.getElementById('interview');
if(ctx){
    new Chart(ctx,{
        type:'bar',
        data:{
            labels:["Technical","Communication","Problem-Solving","Aptitude"],
            datasets:[{
                data: [85, 72, 95, 78],
                backgroundColor:[
                    "#4e73df","#1cc88a",
                    "#f6c23e","#e74a3b"
                ],
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options:{
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: "y",
            plugins:{legend:{display: false}}
        }
    })
}

// Skill Analysis
const ctx1=document.getElementById('skillgap');
if(ctx1){
    const score=Number(ctx1.dataset.score||0);
    new Chart(ctx1, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: ['#084880', '#e8eaee'],
            }]
        },
        options: {
            cutout: '80%',
            devicePixelRatio: window.devicePixelRatio,
            plugins: { legend: { display: false } },
            responsive: true,
            maintainAspectRatio: false
        },
        plugins: [{
            id: 'text',
            beforeDraw: c => {
                let { ctx, chartArea: a } = c;
                let x = (a.left + a.right) / 2;
                let y = (a.top + a.bottom) / 2;
                ctx.save()
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                // Score
                ctx.font = 'bold 22px Arial';
                ctx.fillStyle = '#084880';
                ctx.fillText(`${score}%`, x, y - 7);
                // Remarks
                ctx.font = '16px Arial';
                ctx.fillStyle = '#666';
                ctx.fillText('Skill Match', x, y + 15);
                ctx.restore();
            }
        }]
    });
}

// AI-Match Analysis
const aiMatchElement = document.getElementById("ai_match_data");
if(aiMatchElement){
    const aiMatchData = JSON.parse(aiMatchElement.textContent);
    const ctx2=document.getElementById('aimatch');
    if (ctx2) {
        new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: Object.keys(aiMatchData),
                datasets: [{
                    label: 'Skill Match',
                    data: Object.values(aiMatchData),
                    backgroundColor: [
                        "#e74a3b", "#4e73df", "#1cc88a", "#f6c23e",
                    ],
                    borderWidth: 1,
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "y",
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) { return context.raw + "%"; }
                        }
                    }
                },
            },
        })
    }
}

// Platform Analysis
const platformActivityChart = document.getElementById('platformActivity');
if(platformActivityChart){
    new Chart(platformActivityChart, {
        type: 'line',
        data: {
            labels: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
            datasets: [
                {
                    label: 'Users',
                    data: [120, 180, 150, 230, 280, 250, 320],
                    tension: 0.1,
                    borderColor: '#084880',
                },
                {
                    label: 'AI Requests',
                    data: [240, 360, 280, 420, 390, 450, 510],
                    tension: 0.1,
                    borderColor: '#0A7B76'
                },
            
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// Skill Menu
document.querySelectorAll('.skill-select').forEach((element) => {
    const tomSelect = new TomSelect(element, {
        plugins: ['remove_button'],
        placeholder: 'Choose Skills',
        hidePlaceholder: true,
        create: true,
        maxItems: 6,
        dropdownDirection: 'auto',
    });
});

// Location Menu
document.querySelectorAll('.location-select').forEach((element) => {
    new TomSelect(element, {
        plugins: ['remove_button'],
        placeholder: 'Choose Location',
        hidePlaceholder: true,
        create: true,
        maxItems: 3
    });
});

// Clone Row
document.querySelectorAll(".add-btn").forEach(button => {
    button.addEventListener("click", function () {
        const section = this.closest(".col-md-9");
        const row = section.querySelector(".add-row");
        const newRow = row.cloneNode(true);
        newRow.querySelectorAll("input").forEach(input => {
            input.value = "";
        });
        row.parentNode.appendChild(newRow);
    });
});

document.querySelectorAll(".del-btn").forEach(button => {
    button.addEventListener("click", function () {
        const section = this.closest(".col-md-9");
        const rows = section.querySelectorAll(".add-row");
        if (rows.length > 1) {
            rows[rows.length - 1].remove();
        }
    });
});

const webcam=document.getElementById('webcam')
const placeholder = document.getElementById('webcamPlaceholder');
if (webcam && placeholder) {
    async function startwebcam() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true, audio: false
            });
            webcam.srcObject = stream;
            webcam.style.display='block'
            placeholder.style.display='none'
        } catch (error) {
            webcam.style.display='none';
            placeholder.style.display='flex';
        }
    }
    startwebcam();
}

// AJAX: Mock Interview
const form=document.getElementById("interviewForm");
form.addEventListener("submit",function(e){
    e.preventDefault();
    fetch("",{
        method: 'POST',
        body: new FormData(form),
        headers: {
            'X-Requested-With':'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data=>{
        if (data.completed){
            window.location.href = data.redirect;
            return;
        }
        document.getElementById("questionText").textContent =
            data.question;
        document.getElementById("questionBadge").textContent =
            "Question " + data.question_number;
        document.getElementById("answer").value = "";
    });
});

