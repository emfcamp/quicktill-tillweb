/* Display board for EMF bar */


const header = document.getElementById("title");
const content = document.getElementById("content");
const clock = document.getElementById("clock");
const page = document.getElementById("page");
const fadeTime = 1000; /* Should match the CSS */
const waitTime = 500; /* How long to wait with blank page? */
const recoverTime = 5000; /* How long to wait after network error? */
const defaultHeader = header.innerText;
const defaultContent = content.innerHTML;
const defaultDisplayTime = 10000;

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/* Main display loop */
(async () => {
    var current_header = header.innerText;
    var current_content = content.innerHTML;
    var current_page = page.innerText;
    var current = "start";

    async function display(new_header, new_content, new_page, fade) {
	if (new_header != current_header || new_content != current_content ||
	    new_page != current_page) {
	    if (fade) {
		header.style.opacity = "0";
		content.style.opacity = "0";
		page.style.opacity = "0";
		await sleep(fadeTime + waitTime);
	    }
	    header.innerText = new_header;
	    content.innerHTML = new_content;
	    page.innerText = new_page;
	    current_header = new_header;
	    current_content = new_content;
	    current_page = new_page;
	    if (fade) {
		header.style.opacity = "1";
		content.style.opacity = "1";
		page.style.opacity = "1";
		await sleep(fadeTime);
	    }
	}
    }

    while (true) {
	var res;
	var json;
	try {
	    res = await fetch('info.json?current=' + current);
	} catch (error) {
	    console.error(error);
	    await display(defaultHeader, "Network error; retrying...", "", true);
	    current = "retry-network";
	    await sleep(recoverTime);
	    continue;
	}
	try {
	    json = await res.json();
	} catch (error) {
	    console.error(error);
	    await display(defaultHeader, "Didn't receive JSON; retrying...", "", true);
	    current = "retry-json";
	    await sleep(recoverTime);
	    continue;
	}
	await display(json.header || defaultHeader,
		      json.content || defaultContent,
		      json.page || "",
		      json.name != current);
	current = json.name;
	await sleep(json.duration || defaultDisplayTime);
    }
})();

/* Clock loop */
(async () => {
    while (true) {
	const date = new Date();
	const h = date.getHours().toString().padStart(2, '0');
	const m = date.getMinutes().toString().padStart(2, '0');
	const s = date.getSeconds();

	clock.innerText = h + ':' + m;

	/* We want to wait until just after the minute ticks over */
	await sleep((60 - s) * 1000);
    }
})();
