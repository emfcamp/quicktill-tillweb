/* Display board for EMF bar */


const header = document.getElementById("header");
const content = document.getElementById("content");
const clock = document.getElementById("clock");
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
    var current = "start";

    async function display(new_header, new_content) {
	if (new_header != current_header || new_content != current_content) {
	    header.style.opacity = "0";
	    content.style.opacity = "0";
	    await sleep(fadeTime + waitTime);
	    header.innerText = new_header;
	    content.innerHTML = new_content;
	    current_header = new_header;
	    current_content = new_content;
	    header.style.opacity = "1";
	    content.style.opacity = "1";
	    await sleep(fadeTime);
	}
    }

    while (true) {
	var res;
	var json;
	try {
	    res = await fetch('/display/info.json?current=' + current);
	} catch (error) {
	    console.error(error);
	    await display(defaultHeader, "Network error; retrying...");
	    await sleep(recoverTime);
	    continue;
	}
	try {
	    json = await res.json();
	} catch (error) {
	    console.error(error);
	    await display(defaultHeader, "Didn't receive JSON; retrying...");
	    await sleep(recoverTime);
	    continue;
	}
	await display(json.header || defaultHeader,
		      json.content || defaultContent);
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
