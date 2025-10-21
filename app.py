import os
import re
import json
import requests
from dotenv import load_dotenv
import gradio as gr
import modelscope_studio.components.antd as antd
import modelscope_studio.components.base as ms
import modelscope_studio.components.pro as pro

load_dotenv() 

# ---------- CONFIG ----------
API_KEY=os.getenv("KEY")  # <-- set this env var
MODEL="z-ai/glm-4.5-air:free" # change if you have a specific model on OpenRouter
ENDPOINT ="https://openrouter.ai/api/v1/chat/completions"


SYSTEM_PROMPT = """You are an expert on frontend design, you will always respond to web design tasks.
Your task is to create a website according to the user's request using either native HTML or React framework.
When choosing implementation framework, you should follow these rules:
[Implementation Rules]
1. You should use HTML by default.
2. When the user requires HTML, choose HTML to implement the request.
3. If the user requires a library that is not installed in current react environment, please use HTML and tell the user the reason.
4. After choosing the implementation framework, please follow the corresponding instruction.


[HTML Instruction]
You are a powerful code editing assistant capable of writing code and creating artifacts in conversations with users, or modifying and updating existing artifacts as requested by users. 
All code is written in a single code block to form a complete code file for display, without separating HTML and JavaScript code. An artifact refers to a runnable complete code snippet, you prefer to integrate and output such complete runnable code rather than breaking it down into several code blocks. For certain types of code, they can render graphical interfaces in a UI window. After generation, please check the code execution again to ensure there are no errors in the output.
Do not use localStorage as it is not supported by current environment.
Output only the HTML, without any additional descriptive text.
use cdn links for external libraries.


[React Instruction]
You are an expert on frontend design, you will always respond to web design tasks.
Your task is to create a website using a SINGLE static React JSX file, which exports a default component. This code will go directly into the App.jsx file and will be used to render the website.

## Common Design Principles

Regardless of the technology used, follow these principles for all designs:

### General Design Guidelines:
- Create a stunning, contemporary, and highly functional website based on the user's request
- Implement a cohesive design language throughout the entire website/application
- Choose a carefully selected, harmonious color palette that enhances the overall aesthetic
- Create a clear visual hierarchy with proper typography to improve readability
- Incorporate subtle animations and transitions to add polish and improve user experience
- Ensure proper spacing and alignment using appropriate layout techniques
- Implement responsive design principles to ensure the website looks great on all device sizes
- Use modern UI patterns like cards, gradients, and subtle shadows to add depth and visual interest
- Incorporate whitespace effectively to create a clean, uncluttered design
- For images, use placeholder images from services like https://placehold.co/     
    
## React Design Guidelines

### Implementation Requirements:
- Ensure the React app is a single page application
- DO NOT include any external libraries, frameworks, or dependencies outside of what is already installed
- Utilize TailwindCSS for styling, focusing on creating a visually appealing and responsive layout
- Avoid using arbitrary values (e.g., `h-[600px]`). Stick to Tailwind's predefined classes for consistency
- Use mock data instead of making HTTP requests or API calls to external services
- Utilize Tailwind's typography classes to create a clear visual hierarchy and improve readability
- Ensure proper spacing and alignment using Tailwind's margin, padding, and flexbox/grid classes
- Do not use localStorage as it is not supported by current environment.

### Installed Libraries:
You can use these installed libraries if required.
- **lucide-react**: Lightweight SVG icon library with 1000+ icons. Import as `import { IconName } from "lucide-react"`. Perfect for buttons, navigation, status indicators, and decorative elements.
- **recharts**: Declarative charting library built on D3. Import components like `import { LineChart, BarChart } from "recharts"`. Use for data visualization, analytics dashboards, and statistical displays.
- **framer-motion**: Production-ready motion library for React. Import as `import { motion } from "framer-motion"`. Use for animations, page transitions, hover effects, and interactive micro-interactions.
- **p5.js** : JavaScript library for creative coding and generative art. Usage: import p5 from "p5". Create interactive visuals, animations, sound-driven experiences, and artistic simulations.
- **three, @react-three/fiber, @react-three/drei**: 3D graphics library with React renderer and helpers. Import as `import { Canvas } from "@react-three/fiber"` and `import { OrbitControls } from "@react-three/drei"`. Use for 3D scenes, visualizations, and immersive experiences.

Remember to only return code for the App.jsx file and nothing else. The resulting application should be visually impressive, highly functional, and something users would be proud to showcase.
"""

EXAMPLES = [
    {
        "title":
        "Bouncing ball",
        "description":
        "Make a page in HTML that shows an animation of a ball bouncing in a rotating hypercube.",
    },
    {
        "title": "Pokémon SVG",
        "description":
        "Help me to generate an SVG of 5 Pokémons, include details."
    },
    {
        "title":
        "Strawberry card",
        "description":
        """How many "r"s are in the word "strawberry"? Make a cute little card!"""
    },
    {
        "title":
        "TODO list",
        "description":
        "I want a TODO list that allows me to add tasks, delete tasks, and I would like the overall color theme to be purple."
    },
]

DEFAULT_LOCALE = 'en_US'

DEFAULT_THEME = {
    "token": {
        "colorPrimary": "#6A57FF",
    }
}

react_imports = {
    "react": "https://esm.sh/react@18.2.0",
    "react/": "https://esm.sh/react@18.2.0/",
    "react-dom": "https://esm.sh/react-dom@18.2.0",
    "react-dom/": "https://esm.sh/react-dom@18.2.0/",
    
    # UI and Animation Libraries
    "lucide-react": "https://esm.sh/lucide-react@0.294.0",
    "framer-motion": "https://esm.sh/framer-motion@10.16.4",
    "@heroicons/react": "https://esm.sh/@heroicons/react@2.0.18",
    "tailwind-merge": "https://esm.sh/tailwind-merge@1.14.0",
    "class-variance-authority": "https://esm.sh/class-variance-authority@0.7.0",
    "clsx": "https://esm.sh/clsx@2.0.0",
    
    # Data Visualization
    "recharts": "https://esm.sh/recharts@2.9.0",
    "d3": "https://esm.sh/d3@7.8.5",
    
    # Creative and 3D Libraries
    "p5": "https://esm.sh/p5@1.7.0",
    "three": "https://esm.sh/three@0.158.0",
    "@react-three/fiber": "https://esm.sh/@react-three/fiber@8.15.11",
    "@react-three/drei": "https://esm.sh/@react-three/drei@9.88.7",
    
    # Canvas and Graphics
    "konva": "https://esm.sh/konva@9.2.3",
    "react-konva": "https://esm.sh/react-konva@18.2.10",
    
    # Physics and Simulation
    "matter-js": "https://esm.sh/matter-js@0.19.0",
    
    # Styling and UI Utils
    "@tailwindcss/browser": "https://esm.sh/@tailwindcss/browser@0.4.0",
    "tailwindcss": "https://esm.sh/tailwindcss@3.3.5",
    "@tailwindcss/typography": "https://esm.sh/@tailwindcss/typography@0.5.10",
    
    # State Management
    "zustand": "https://esm.sh/zustand@4.4.6",
    "jotai": "https://esm.sh/jotai@2.5.1",
    
    # Utils and Helpers
    "date-fns": "https://esm.sh/date-fns@2.30.0",
    "lodash": "https://esm.sh/lodash@4.17.21",
    "uuid": "https://esm.sh/uuid@9.0.1",
    
    # Form Handling
    "react-hook-form": "https://esm.sh/react-hook-form@7.48.2",
    "zod": "https://esm.sh/zod@3.22.4"
}

# ---------- UTIL ----------
def get_generated_files(text):
    patterns = {
        'html': r'```html\n(.+?)\n```',
        'jsx': r'```jsx\n(.+?)\n```',
        'tsx': r'```tsx\n(.+?)\n```',
        'ts': r'```ts\n(.+?)\n```',
        'js': r'```js\n(.+?)\n```',
    }
    result = {}
    for ext, pattern in patterns.items():
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            content = '\n'.join(matches).strip()
            # pick canonical filename
            filename = "index." + ("tsx" if ext in ["tsx", "jsx"] else ext)
            result[filename] = content
    if len(result) == 0:
        result["index.html"] = text.strip()
    return result


def call_openrouter_chat(messages, model=MODEL, endpoint=ENDPOINT, api_key=API_KEY):
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is not set.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        # you can tune max_tokens, temperature, etc. if needed
        # "max_tokens": 1600,
        "temperature": 0.9,
    }
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


# ---------- EVENTS CLASS ----------
class GradioEvents:

    @staticmethod
    def generate_code(input_value, system_prompt_input_value, state_value):

        # initial UI state while we call the API
        yield {
            output_loading: gr.update(spinning=True),
            state_tab: gr.update(active_key="loading"),
            output: gr.update(value=None)
        }

        if input_value is None:
            input_value = ""

        # Build messages: keep history, ensure system prompt presence
        messages = [{
            "role": "system",
            "content": SYSTEM_PROMPT+" always use html if user not specifies any thing make sure u dont use black as background color" if not system_prompt_input_value else system_prompt_input_value
        }] + state_value.get("history", [])

        messages.append({"role": "user", "content": input_value})

        try:
            data = call_openrouter_chat(messages=messages)
        except Exception as e:
            err_text = f"Error contacting OpenRouter API: {str(e)}"
            # set state and show error
            state_value["history"] = messages + [{"role": "assistant", "content": err_text}]
            yield {
                output: gr.update(value=err_text),
                state_tab: gr.update(active_key="render"),
                output_loading: gr.update(spinning=False),
                state: gr.update(value=state_value)
            }
            return

        # Attempt to extract assistant content robustly
        assistant_content = None
        try:
            # Common OpenRouter shape: choices[0].message.content
            if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if isinstance(choice, dict) and "message" in choice and isinstance(choice["message"], dict):
                    assistant_content = choice["message"].get("content") or choice["message"].get("text")
                # fallback: direct 'text' or 'content' fields
                if not assistant_content:
                    assistant_content = choice.get("text") or choice.get("content")
            # final fallback: top-level 'text' or 'generated_text'
            if not assistant_content:
                assistant_content = data.get("text") or data.get("generated_text") or json.dumps(data)
        except Exception:
            assistant_content = json.dumps(data)

        # update history
        state_value["history"] = messages + [{"role": "assistant", "content": assistant_content}]

        generated_files = get_generated_files(assistant_content)
        react_code = generated_files.get("index.tsx") or generated_files.get("index.jsx") or generated_files.get("index.js")
        html_code = generated_files.get("index.html")

        # Completed - return UI update
        yield {
            output: gr.update(value=assistant_content),
            download_content: gr.update(value=react_code or html_code),
            state_tab: gr.update(active_key="render"),
            output_loading: gr.update(spinning=False),
            sandbox: gr.update(
                template="react" if react_code else "html",
                imports=react_imports if react_code else {},
                value={
                    "./index.tsx": """import Demo from './demo.tsx'
import "@tailwindcss/browser"

export default Demo
""",
                    "./demo.tsx": react_code
                } if react_code else {"./index.html": html_code}),
            state: gr.update(value=state_value)
        }

    @staticmethod
    def select_example(example: dict):
        return lambda: gr.update(value=example["description"])

    @staticmethod
    def close_modal():
        return gr.update(open=False)

    @staticmethod
    def open_modal():
        return gr.update(open=True)

    @staticmethod
    def disable_btns(btns: list):
        return lambda: [gr.update(disabled=True) for _ in btns]

    @staticmethod
    def enable_btns(btns: list):
        return lambda: [gr.update(disabled=False) for _ in btns]

    @staticmethod
    def update_system_prompt(system_prompt_input_value, state_value):
        state_value["system_prompt"] = system_prompt_input_value
        return gr.update(value=state_value)

    @staticmethod
    def reset_system_prompt(state_value):
        return gr.update(value=state_value["system_prompt"])

    @staticmethod
    def render_history(statue_value):
        return gr.update(value=statue_value["history"])

    @staticmethod
    def clear_history(state_value):
        # modelscope_studio may have a toast; if not, this still works
        try:
            antd.message.success("History Cleared.")
        except Exception:
            pass
        state_value["history"] = []
        return gr.update(value=state_value)


# ---------- CSS ----------
css = """
/* Full screen container adjustments */
.gradio-container {
    max-width: 100% !important;
    padding: 0 !important;
}

#coder-artifacts {
    min-height: 100vh;
    padding: 1rem;
}

/* Output container adjustments */
#coder-artifacts .output-empty,
#coder-artifacts .output-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 85vh;
}

#coder-artifacts #output-container {
    height: 85vh !important;
}

#coder-artifacts #output-container .ms-gr-ant-tabs-content,
#coder-artifacts #output-container .ms-gr-ant-tabs-tabpane {
    height: 100%;
}

#coder-artifacts .output-html {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    min-height: 85vh;
}

#coder-artifacts .output-html > iframe {
    flex: 1;
    min-height: 85vh;
}

/* Code drawer adjustments */
#coder-artifacts-code-drawer {
    height: 100vh !important;
}

#coder-artifacts-code-drawer .output-code {
    flex: 1;
    height: 100%;
}

#coder-artifacts-code-drawer .output-code .ms-gr-ant-spin-nested-loading {
    min-height: 100%;
}

/* History drawer adjustments */
.history_chatbot {
    height: 85vh !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    #coder-artifacts {
        padding: 0.5rem;
    }
    
    #coder-artifacts #output-container,
    #coder-artifacts .output-html,
    #coder-artifacts .output-html > iframe {
        min-height: 70vh;
    }
}
"""

# ---------- GRADIO UI ----------
with gr.Blocks(css=css) as demo:
    # Global State
    state = gr.State({"system_prompt": "", "history": []})
    with ms.Application(elem_id="coder-artifacts") as app:
        with antd.ConfigProvider(theme=DEFAULT_THEME, locale=DEFAULT_LOCALE):
            with ms.AutoLoading():
                with antd.Row(gutter=[32, 12],
                              elem_style=dict(marginTop=20),
                              align="stretch"):
                    # Left Column
                    with antd.Col(span=24, md=8):
                        with antd.Flex(vertical=True, gap="middle", wrap=True):
                            with antd.Flex(justify="center",
                                           align="center",
                                           vertical=True,
                                           gap="middle"):
                                # antd.Image(
                                #     "https://img.alicdn.com/imgextra/i2/O1CN01KDhOma1DUo8oa7OIU_!!6000000000220-1-tps-240-240.gif",
                                #     width=200,
                                #     height=200,
                                #     preview=False)
                                antd.Typography.Title(
                                    "My-v0",
                                    level=1,
                                    elem_style=dict(fontSize=24))
                            # Input
                            input = antd.Input.Textarea(
                                size="large",
                                allow_clear=True,
                                auto_size=dict(minRows=2, maxRows=6),
                                placeholder=
                                "Describe the web application you want to create",
                                elem_id="input-container")
                            # Input Notes
                            with antd.Flex(justify="space-between"):
                                antd.Typography.Text(
                                    "Note: The model supports multi-round dialogue, you can make the model generate interfaces by returning React or HTML code.",
                                    strong=True,
                                    type="warning")

                                tour_btn = antd.Button("Usage Tour",
                                                       variant="filled",
                                                       color="default")
                            # Submit Button
                            submit_btn = antd.Button("Submit",
                                                     type="primary",
                                                     block=True,
                                                     size="large",
                                                     elem_id="submit-btn")

                            antd.Divider("Settings")

                            # Settings Area
                            with antd.Space(size="small",
                                            wrap=True,
                                            elem_id="settings-area"):
                                history_btn = antd.Button(
                                    "📜 History",
                                    type="default",
                                    elem_id="history-btn",
                                )
                                cleat_history_btn = antd.Button(
                                    "🧹 Clear History", danger=True)

                            antd.Divider("Examples")

                            # Examples
                            with antd.Flex(gap="small", wrap=True):
                                for example in EXAMPLES:
                                    with antd.Card(
                                            elem_style=dict(
                                                flex="1 1 fit-content"),
                                            hoverable=True) as example_card:
                                        antd.Card.Meta(
                                            title=example['title'],
                                            description=example['description'])

                                    example_card.click(
                                        fn=GradioEvents.select_example(
                                            example),
                                        outputs=[input])

                    # Right Column
                    with antd.Col(span=24, md=16):
                        with antd.Card(
                                title="Output",
                                elem_style=dict(
                                    height="85vh",
                                    display="flex",
                                    flexDirection="column",
                                    margin=0,
                                    borderRadius="8px",
                                    boxShadow="0 4px 6px -1px rgb(0 0 0 / 0.1)"
                                ),
                                styles=dict(
                                    body=dict(
                                        height=0,
                                        flex=1,
                                        padding=0
                                    )
                                ),
                                elem_id="output-container"):
                            # Output Container Extra
                            with ms.Slot("extra"):
                                with ms.Div(elem_id="output-container-extra"):
                                    with antd.Button(
                                            "Download Code",
                                            type="link",
                                            href_target="_blank",
                                            disabled=True,
                                    ) as download_btn:
                                        with ms.Slot("icon"):
                                            antd.Icon("DownloadOutlined")
                                    download_content = gr.Text(visible=False)

                                    view_code_btn = antd.Button(
                                        "🧑‍💻 View Code", type="primary")
                            # Output Content
                            with antd.Tabs(
                                    elem_style=dict(height="100%"),
                                    active_key="empty",
                                    render_tab_bar="() => null") as state_tab:
                                with antd.Tabs.Item(key="empty"):
                                    antd.Empty(
                                        description=
                                        "Enter your request to generate code",
                                        elem_classes="output-empty")
                                with antd.Tabs.Item(key="loading"):
                                    with antd.Spin(
                                            tip="Generating code...",
                                            size="large",
                                            elem_classes="output-loading"):
                                        # placeholder
                                        ms.Div()
                                with antd.Tabs.Item(key="render"):
                                    sandbox = pro.WebSandbox(
                                        height="100%",
                                        elem_classes="output-html",
                                        template="html",
                                    )

                    # Modals and Drawers
                    with antd.Modal(open=False,
                                    title="System Prompt",
                                    width="800px") as system_prompt_modal:
                        system_prompt_input = antd.Input.Textarea(
                            value="",
                            size="large",
                            placeholder="Enter your system prompt here",
                            allow_clear=True,
                            auto_size=dict(minRows=4, maxRows=14))

                    with antd.Drawer(
                            open=False,
                            title="Output Code",
                            placement="right",
                            get_container=
                            "() => document.querySelector('.gradio-container')",
                            elem_id="coder-artifacts-code-drawer",
                            styles=dict(
                                body=dict(display="flex",
                                          flexDirection="column-reverse")),
                            width="750px") as output_code_drawer:
                        with ms.Div(elem_classes="output-code"):
                            with antd.Spin(spinning=False) as output_loading:
                                output = ms.Markdown()

                    with antd.Drawer(
                            open=False,
                            title="Chat History",
                            placement="left",
                            get_container=
                            "() => document.querySelector('.gradio-container')",
                            width="750px") as history_drawer:
                        history_output = gr.Chatbot(
                            show_label=False,
                            type="messages",
                            height='100%',
                            elem_classes="history_chatbot")
                    # Tour
                    with antd.Tour(open=False) as usage_tour:
                        antd.Tour.Step(
                            title="Step 1",
                            description=
                            "Describe the web application you want to create.",
                            get_target=
                            "() => document.querySelector('#input-container')")
                        antd.Tour.Step(
                            title="Step 2",
                            description="Click the submit button.",
                            get_target=
                            "() => document.querySelector('#submit-btn')")
                        antd.Tour.Step(
                            title="Step 3",
                            description="Wait for the result.",
                            get_target=
                            "() => document.querySelector('#output-container')"
                        )
                        antd.Tour.Step(
                            title="Step 4",
                            description=
                            "Download the generated HTML here or view the code.",
                            get_target=
                            "() => document.querySelector('#output-container-extra')"
                        )
                        antd.Tour.Step(
                            title="Additional Settings",
                            description="You can change chat history here.",
                            get_target=
                            "() => document.querySelector('#settings-area')")

    # Event Handler wiring
    gr.on(fn=GradioEvents.close_modal,
          triggers=[usage_tour.close, usage_tour.finish],
          outputs=[usage_tour])
    tour_btn.click(fn=GradioEvents.open_modal, outputs=[usage_tour])

    system_prompt_modal.ok(GradioEvents.update_system_prompt,
                           inputs=[system_prompt_input, state],
                           outputs=[state]).then(fn=GradioEvents.close_modal,
                                                 outputs=[system_prompt_modal])

    system_prompt_modal.cancel(GradioEvents.close_modal,
                               outputs=[system_prompt_modal]).then(
                                   fn=GradioEvents.reset_system_prompt,
                                   inputs=[state],
                                   outputs=[system_prompt_input])
    output_code_drawer.close(fn=GradioEvents.close_modal,
                             outputs=[output_code_drawer])
    cleat_history_btn.click(fn=GradioEvents.clear_history,
                            inputs=[state],
                            outputs=[state])
    history_btn.click(fn=GradioEvents.open_modal,
                      outputs=[history_drawer
                               ]).then(fn=GradioEvents.render_history,
                                       inputs=[state],
                                       outputs=[history_output])
    history_drawer.close(fn=GradioEvents.close_modal, outputs=[history_drawer])

    download_btn.click(fn=None,
                       inputs=[download_content],
                       js="""(content) => {
        const blob = new Blob([content], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'output.txt'
        a.click()
}""")
    view_code_btn.click(fn=GradioEvents.open_modal,
                        outputs=[output_code_drawer])
    submit_btn.click(
        fn=GradioEvents.open_modal,
        outputs=[output_code_drawer],
    ).then(fn=GradioEvents.disable_btns([submit_btn, download_btn]),
           outputs=[submit_btn, download_btn]).then(
               fn=GradioEvents.generate_code,
               inputs=[input, system_prompt_input, state],
               outputs=[
                   output, state_tab, sandbox, download_content,
                   output_loading, state
               ]).then(fn=GradioEvents.enable_btns([submit_btn, download_btn]),
                       outputs=[submit_btn, download_btn
                                ]).then(fn=GradioEvents.close_modal,
                                        outputs=[output_code_drawer])

if __name__ == "__main__":
    # tune queue params as you like
    demo.queue(default_concurrency_limit=10, max_size=50).launch(ssr_mode=False, max_threads=100)
