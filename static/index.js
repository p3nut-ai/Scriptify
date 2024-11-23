let isProcessing = false;
console.log("sampole");
const handleProcess = async () => {
  const button = document.getElementById("processButton");
  const actionSelect = document.querySelector("select");

  if (!actionSelect.value) {
    return; // Do nothing if no option is selected
  }

  isProcessing = true;
  button.disabled = true;
  button.innerHTML = '<svg class="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 2a10 10 0 100 20 10 10 0 000-20zm0 18a8 8 0 110-16 8 8 0 010 16z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg> Processing...'; // Show loading spinner

  // Simulate processing (e.g., 2 seconds)
  await new Promise(resolve => setTimeout(resolve, 2000));

  isProcessing = false;
  button.disabled = false;
  button.setAttribute("class","bg-green-600 min-w-[50px]  px-2 py-2 text-sm text-white font-semibold rounded-lg disabled:bg-gray-300 flex items-center justify-center space-x-2");
  button.innerHTML = '<p class="pl-2 pr-2">Done</p>'; // Reset button text
};
