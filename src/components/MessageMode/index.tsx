import { useState, useEffect, useRef } from "react";
import Message from "./Message";
import Image from "next/image";

interface MessageProps {
  type: string;
  message: string;
}

export default function MessageMode() {
  const [text, setText] = useState<string>("");
  const [currentMessage, setCurrentMessage] = useState<any>("");
  const [endReached, setEndReached] = useState<boolean>(false);
  const [latestMessage, setLatestMessage] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [showResponse, setShowResponse] = useState<boolean>(false);
  const [latestImage, setLatestImage] = useState<string>(""); // Store the latest image value
  const [selectedOption, setSelectedOption] = useState<string>("OpenAI"); // Selected option in dropdown
  const inputRef = useRef<HTMLInputElement>(null);
  const messageRef = useRef<any>(null);

  useEffect(() => {
    if (messageRef.current) {
      messageRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [latestMessage]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  useEffect(() => {
    if (endReached) {
      setLatestMessage({ type: "ai", message: currentMessage });
      setCurrentMessage("");
      setEndReached(false);
      setIsGenerating(false);
      setShowResponse(true);
    }
  }, [endReached]);

  useEffect(() => {
    //@ts-ignore
    window.electronAPI.on("receiveTokens", (event, arg) => {
      setCurrentMessage(arg);
      setIsGenerating(true);
      setShowResponse(false);
      // Immediately clear any previous message when new tokens start coming in
      setLatestMessage(null);
    });

    //@ts-ignore
    window.electronAPI.on("endTokens", (event, arg) => {
      setEndReached(true);
    });

    //@ts-ignore
    window.electronAPI.on("setLatestImage", (event, image) => {
      setLatestImage(image); // Set the latest image value received from the main process
    });
  }, []);

  // Dropdown options
  const options = [
    { value: "OpenAI", label: "OpenAI" },
    { value: "Phi", label: "Phi" },
    { value: "Gemma", label: "Gemma" },
    { value: "Ollama", label: "Ollama" },
  ];

  const handleOptionChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedOption(event.target.value);
  };

  const handleNewQuery = (e: React.FormEvent) => {
    e.preventDefault();
    const messageToSend = selectedOption + "$!$" + text;
    console.log(messageToSend);
    //@ts-ignore
    window.electronAPI.send("sendChat", messageToSend);
    setText("");
    setIsGenerating(true);
    setShowResponse(false);
    // Clear previous response when starting a new query
    setLatestMessage(null);
  };

  return (
    <>
      {/* Full-screen background */}
      <div className="fixed inset-0 h-full w-full bg-cover bg-center" style={{ backgroundImage: 'url("/images/background.jpg")' }}>
        {/* Semi-transparent overlay with light gradient */}
        {/* <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-black/5 backdrop-blur-[0.5px]"></div> */}
      </div>
      
      {/* Response area - only shown when there's a response to display and not generating new response */}
      {showResponse && latestMessage && !isGenerating && (
        <div className="fixed inset-0 flex items-center justify-center pointer-events-none z-10">
          <div className="w-full max-w-3xl mx-auto pointer-events-auto">
            <Message 
              type="ai" 
              message={latestMessage.message} 
            />
            <div ref={messageRef} />
          </div>
        </div>
      )}
      
      {/* Input bar - always visible at bottom */}
      <form
        onSubmit={handleNewQuery}
        className="fixed bottom-8 left-0 w-full flex justify-center items-center z-20"
      >
        <div className={`w-full max-w-lg mx-auto p-3 bg-transparent backdrop-blur-md flex rounded-full relative ${isGenerating ? 'border-transparent' : 'border border-white/20'} flex-row justify-between items-center shadow-lg transition-all duration-200 hover:shadow-xl overflow-hidden`}>
          {/* Animated Progress Border */}
          {isGenerating && (
            <div className="absolute inset-0 rounded-full overflow-hidden">
              <div className="absolute inset-0 -z-10 border border-white/40 rounded-full"></div>
              <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 border-white/60 rounded-full animate-progress"></div>
            </div>
          )}
          <div className="pl-3 flex items-center"></div>
          <input
            ref={inputRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            type="text"
            className="text-base mx-3 bg-transparent rounded-full font-normal text-white/90 flex-1 border-none focus:outline-none focus:ring-0 placeholder-white/50"
            placeholder="What ya wanna know?"
          />
          <div 
            className="pr-3 cursor-pointer rounded-full hover:bg-white/10 p-1.5 transition-colors"
            onClick={() => {
              // Toggle through available models when clicking this button
              const currentIndex = options.findIndex(option => option.value === selectedOption);
              const nextIndex = (currentIndex + 1) % options.length;
              setSelectedOption(options[nextIndex].value);
            }}
          >
            <Image
              src={`/images/${selectedOption}.png`}
              height={20}
              width={20}
              alt={`${selectedOption} Model`}
              className="rounded-full"
            />
          </div>
        </div>
      </form>
    </>
  );
}
