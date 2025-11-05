document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('analyze-form');
    const input = document.getElementById('topic-input');
    const button = document.getElementById('submit-button');
    const loadingDiv = document.getElementById('loading');
    const statusP = document.getElementById('status');
    const resultsContainer = document.getElementById('results-container');
    const factsContent = document.getElementById('key-facts-content');
    const analysisContent = document.getElementById('final-analysis-content');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const topic = input.value.trim();
        if (!topic) return;

        button.disabled = true;
        button.textContent = 'В процессе...';
        resultsContainer.classList.add('hidden');
        loadingDiv.classList.remove('hidden');
        statusP.textContent = 'Запускаю агентов...';

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic: topic })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Произошла ошибка на сервере');
            }

            const data = await response.json();

            // Отображение результатов
            let factsHtml = '<ul>';
            data.key_facts.forEach(fact => {
                let dateHtml = fact.published_date ? `<span class="date">(${fact.published_date})</span>` : '';
                factsHtml += `<li>${fact.fact} <a href="${fact.source_url}" target="_blank">[источник]</a> ${dateHtml}</li>`;
            });
            factsHtml += '</ul>';
            factsContent.innerHTML = factsHtml;

            analysisContent.innerHTML = marked.parse(data.final_analysis);

            resultsContainer.classList.remove('hidden');

        } catch (error) {
            statusP.textContent = `Ошибка: ${error.message}`;
        } finally {
            loadingDiv.classList.add('hidden');
            button.disabled = false;
            button.textContent = 'Проанализировать';
        }
    });
});
