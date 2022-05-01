/* Display board for EMF bar */


const header = document.getElementById("header");
const content = document.getElementById("content");
const fadeTime = 1000; /* Should match the CSS */
const waitTime = 500; /* How long to wait with blank page? */
const recoverTime = 5000; /* How long to wait after network error? */
const defaultHeader = "EMF Bar Information";
const defaultContent = "Missing content";
const defaultDisplayTime = 10000;

function show() {
    header.style.opacity = "1";
    content.style.opacity = "1";
}

function hide() {
    header.style.opacity = "0";
    content.style.opacity = "0";
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/* In a loop, we want to:
 *  * fetch from /display/info.json
 *  * hide() the current display
 *  * set header and content
 *  * show() the new display
 *  * delay specified time (or default)
 *  * repeat from start
 */

(async () => {
    var current = "start";
    var displayOK = true;
    await sleep(waitTime);
    while (true) {
	var res;
	var json;
	try {
	    res = await fetch('/display/info.json?current=' + current);
	} catch (error) {
	    console.error(error);
	    if (displayOK) {
		displayOK = false;
		hide();
		await sleep(fadeTime + waitTime);
		header.innerText = "EMF Bar Information";
		content.innerText = "Network error; retrying...";
		show();
	    }
	    await sleep(recoverTime);
	    continue;
	}
	try {
	    json = await res.json();
	} catch (error) {
	    console.error(error);
	    if (displayOK) {
		displayOK = false;
		hide();
		await sleep(fadeTime + waitTime);
		header.innerText = "EMF Bar Information";
		content.innerText = "Didn't receive JSON; retrying...";
		show();
		current = "start";
	    }
	    await sleep(recoverTime);
	    continue;
	}
	hide();
	await sleep(fadeTime + waitTime);
	header.innerText = json.header || defaultHeader;
	content.innerHTML = json.content || defaultContent;
	current = json.name;
	displayOK = true;
	show();
	await sleep(fadeTime + (json.duration || defaultDisplayTime));
    }
})();
