async function sendAIRequest(url, options, loadingMessage) {

    try {

        showLoader(loadingMessage);

        const response = await fetch(url, options);

        const data = await response.json();

        hideLoader();

        return data;

    }

    catch(error){

        hideLoader();

        alert("Something went wrong.");

        console.error(error);

        return null;

    }

}