document.getElementById('analyzeBtn').addEventListener('click', function () {
    const url = document.getElementById('youtubeUrl').value;

    if (!url) {
        alert('Please enter a YouTube URL');
        return;
    }

    // Show loading spinner
    document.querySelector('.loading-spinner').style.display = 'block';
    document.getElementById('resultContainer').innerHTML = '';
    if (document.getElementById('aiVerdictContainer')) {
        document.getElementById('aiVerdictContainer').innerHTML = '';
    }

    // Simulate API call delay
    // Make the actual API call to your Flask back-end
    fetch(`http://127.0.0.1:5000/analyze?url=${encodeURIComponent(url)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(randomResult => {
            // Hide loading spinner
            document.querySelector('.loading-spinner').style.display = 'none';

            // Format views for display
            const views = randomResult.views;
            const viewsDisplay = views >= 1000000
                ? (views / 1000000).toFixed(1) + "M"  // Convert to million format with 1 decimal place
                : views.toLocaleString();             // Otherwise, show the number with commas

            // Display results (The structure of the result is what the Python script returns)
            const resultHTML = `
                    <div class="result-card result-${randomResult.type}">
                        <div class="text-center">
                            <div class="result-icon">
                                <i class="fas ${randomResult.icon}"></i>
                            </div>
                            <h3 class="result-title">${randomResult.title}</h3>
                            <p class="lead">${randomResult.description}</p>
                            
                            <div class="row mt-4">
                                <div class="col-md-3">
                                    <div class="metric-card">
                                        <div class="metric-value">${randomResult.sentiment}%</div>
                                        <div class="metric-label">Positive Sentiment</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="metric-card">
                                        <div class="metric-value">${randomResult.engagement}%</div>
                                        <div class="metric-label">Engagement Rate</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="metric-card">
                                        <div class="metric-value">${randomResult.likes.toLocaleString()}</div>
                                        <div class="metric-label">Likes</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="metric-card">
                                        <div class="metric-value">${viewsDisplay}</div>
                                        <div class="metric-label">Views</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-4">
                                <small class="text-muted">Analysis based on comment sentiment and engagement metrics</small>
                            </div>
                        </div>
                    </div>
                `;

            document.getElementById('resultContainer').innerHTML = resultHTML;
            document.querySelector('.result-card').style.display = 'block';

            if (randomResult.ai_verdict && document.getElementById('aiVerdictContainer')) {
                const verdictHTML = `
                    <div class="alert alert-info shadow-sm text-start">
                        <h4 class="alert-heading"><i class="fas fa-robot me-2"></i>AI Content Verdict</h4>
                        <p class="mb-0 fs-5">${randomResult.ai_verdict}</p>
                    </div>
                `;
                document.getElementById('aiVerdictContainer').innerHTML = verdictHTML;
            }
        })
        .catch(error => {
            console.error('Analysis failed:', error);
            document.querySelector('.loading-spinner').style.display = 'none';
            document.getElementById('resultContainer').innerHTML = `<div class="alert alert-danger">Error: Could not connect to the analysis server. Make sure your 'app.py' is running.</div>`;
        });
});