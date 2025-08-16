function uploadResume() {
    let fileInput = document.getElementById('resumeInput');
    if (fileInput.files.length === 0) {
        alert("Please select a file first!");
        return;
    }

    let formData = new FormData();
    formData.append("resume", fileInput.files[0]);

    fetch("/analyze", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        let chatBody = document.getElementById('chatBody');

        if (data.error) {
            chatBody.innerHTML += `<div class="message bot">${data.error}</div>`;
        } else {
            data.results.forEach(r => {
                let msg = `
                <div class="message bot result-card">
                    <div class="result-title">
                        🎯 Predicted Role: <span class="role-name">${r.role}</span> 
                        <span class="confidence">(${r.confidence}% match)</span>
                    </div>
                    <div class="matched-skills">
                        ✅ <b>Matched Skills:</b> ${r.matched_skills.length > 0 ? r.matched_skills.join(", ") : "None"}
                    </div>
                    <div class="missing-skills">
                        ❌ <b>Missing Skills:</b> ${r.missing_skills.length > 0 ? r.missing_skills.join(", ") : "None"}
                    </div>`;

                if (r.recommended_courses.length > 0) {
                    msg += `<div class="recommended-courses">
                            📚 <b>Recommended Courses:</b>
                            <ul>`;
                    r.recommended_courses.forEach(c => {
                        msg += `<li><strong>${c.skill}</strong>: <a href="${c.link}" target="_blank">${c.course}</a> (${c.platform})</li>`;
                    });
                    msg += `</ul></div>`;
                }

                msg += `</div>`;
                chatBody.innerHTML += msg;
            });
        }

        chatBody.scrollTop = chatBody.scrollHeight;
    })
    .catch(err => console.error(err));
}
