// Dans sendChatMessage()
try {
    const result = await apiCall("/chat", "POST", { question });
    loadingDiv.remove();
    
    if (result) {
        if (result.sql === null && result.data.length === 0) {
            // Réponse sans données (hors sujet ou refus)
            addChatMessage('bot', result.answer);
        } else {
            addChatMessage('bot', result.answer, result.sql);
            if (result.data && result.data.length > 0) {
                // Afficher les données
            }
        }
    }
} catch (error) {
    loadingDiv.remove();
    addChatMessage('bot', `❌ Erreur: ${error.message || 'Problème de connexion au serveur'}`);
}