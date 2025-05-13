import { useEffect, useMemo, useState } from "react";
import Markdown from "markdown-to-jsx";
import Image from "next/image";

interface Props {
  type: string;
  message: string;
}

function ModelMessage({ message }: Props) {
  const [value, setValue] = useState<any>([]);

  const { modelName, imageUrl } = useMemo(() => {
    if (!message) return { modelName: "", imageUrl: "" };

    const parts = message.split("$!$");
    const second_parts = parts[1].split("^@^");
    const model = String(second_parts[0].slice(0, -1)).toLowerCase();
    let modelName = "";
    let imageUrl = "";

    switch (model) {
      case "phi":
        modelName = "Phi-3 Multimodal";
        imageUrl = "/images/Phi.png";
        break;
      case "openai":
        modelName = "GPT-4o";
        imageUrl = "/images/OpenAI.png";
        break;
      case "ollama":
        modelName = "Ollama";
        imageUrl = "/images/Ollama.png";
        break;
      default:
        modelName = "Gemma";
        imageUrl = "/images/Gemma.png";
        break;
    }

    return { modelName, imageUrl };
  }, [message]);

  const speed = useMemo(() => {
    return Number(message.split("^@^")[1]);
  }, [message]);

  const updatedMessage = useMemo(() => {
    if (!message) return "";
    const parts = message.split("$!$");
    return parts[0];
  }, [message]);

  if (!message) return null;

  return (
    <div className="flex flex-col space-y-3 w-full max-w-2xl px-6 py-5 bg-transparent backdrop-blur-md rounded-3xl mx-auto border border-white/20 animate-fade-in shadow-lg mb-8">
      <div className="text-white mt-1">
        <Markdown
          options={{
            overrides: {
              b: {
                component: ({ children, ...props }) => <strong {...props} className="text-white">{children}</strong>,
              },
              i: {
                component: ({ children, ...props }) => <em {...props} className="text-white">{children}</em>,
              },
              code: {
                component: ({ children, ...props }) => (
                  <pre {...props} className="language-python bg-transparent p-2 rounded border border-white/10">
                    <code className="text-xs break-all text-white">{children}</code>
                  </pre>
                ),
              },
              ul: {
                component: ({ children, ...props }) => (
                  <ul {...props} className="text-base ml-5 list-disc mt-1 text-white">
                    {children}
                  </ul>
                ),
              },
              li: {
                component: ({ children, ...props }) => (
                  <li {...props} className="text-base mt-0.5 text-white">
                    {children}
                  </li>
                ),
              },
              p: {
                component: ({ children, ...props }) => (
                  <p {...props} className="text-base my-2 text-white leading-relaxed">
                    {children}
                  </p>
                ),
              },
              h1: {
                component: ({ children, ...props }) => (
                  <h1 {...props} className="text-xl mt-3 font-bold text-white">
                    {children}
                  </h1>
                ),
              },
            },
          }}
        >
          {updatedMessage}
        </Markdown>
      </div>
      <div className="mt-3 flex flex-row justify-end items-center w-full text-gray-400 border-t border-gray-700/30 pt-2">
        <p className="text-sm font-mono text-white/70">{speed ? `${speed.toFixed(2)} tokens/sec` : ''}</p>
      </div>
    </div>
  );
}

function UserMessage({ message }: Props) {
  return null;
}

export default function Message({ type, message }: Props) {
  return (
    <>
      {type == "user" ? <UserMessage type={type} message={message} /> : <ModelMessage type={type} message={message} />}
    </>
  );
}
