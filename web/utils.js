export function setupFileLoader(fileInputId, textareaId) {
    const input = document.getElementById(fileInputId);
    const area = document.getElementById(textareaId);
    if (!input || !area) {
        return;
    }
    input.addEventListener('change', async () => {
        const file = input.files[0];
        if (!file) {
            return;
        }
        const text = await file.text();
        area.value = text;
    });
}
