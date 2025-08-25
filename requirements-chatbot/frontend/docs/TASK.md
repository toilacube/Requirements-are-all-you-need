
### **Phase 4: Implementation Plan**

This is a checklist of concrete tasks to help you start building the chatbot application. The plan is divided into logical stages, from setup to completion.

---

#### **Phase 1: Project Setup and Foundation**

*Goal: Prepare the development environment and necessary libraries.*

1. **Initialize Project:**

   * Create a new React project with Vite and TypeScript.
   * Command:

     ```bash
     pnpm create vite my-chatbot --template react-ts
     ```
2. **Install Tailwind CSS:**

   * Follow the official guide to integrate Tailwind CSS into the Vite project.
3. **Install shadcn/ui:**

   * Run

     ```bash
     pnpm dlx shadcn-ui@latest init
     ```

     to set up `shadcn/ui`, configure `tailwind.config.js`, and generate `components.json`.
4. **Add Required Components:**

   * Add the predefined UI components from `shadcn/ui`.
   * Command:

     ```bash
     pnpm dlx shadcn@latest add card input button scroll-area avatar alert-dialog alert
     ```
5. **Create Project Structure:**

   * Create folders as per the design:
     `src/components/chat`, `src/hooks`, `src/services`.

---

#### **Phase 2: Core Logic (Custom Hook & Service)**

*Goal: Build the “brain” of the application before the UI.*

1. **Define Interfaces:**

   * In `src/services/chatService.ts`, define the `ChatMessage` interface.
2. **Create Chat Service:**

   * In `chatService.ts`, implement `streamChatResponse` to call the API via `fetch`, handle **Server-Sent Events (SSE)**, and support callbacks (`onToken`, `onComplete`, `onError`).
3. **Set up Custom Hook `useChat`:**

   * Create `src/hooks/useChat.ts`.
   * Define states: `messages`, `isLoading`, `error`.
4. **Integrate Local Storage:**

   * In `useChat.ts`, load messages from Local Storage when the hook initializes (using `useEffect`).
   * Save the **last 50 messages** back to Local Storage whenever `messages` changes.
5. **Finalize Hook Logic:**

   * Implement `sendMessage` to update state, call `streamChatResponse`, and handle callbacks for tokens/errors/completion.
   * Implement `clearChat` to reset `messages` state and Local Storage.

---

#### **Phase 3: UI Components**

*Goal: Build React components for displaying data and user interaction.*

1. **`MessageItem.tsx`:**

   * Accepts `message: ChatMessage` as a prop.
   * Displays message content with an `Avatar`.
   * Applies different styles for `user` vs `assistant`.
2. **`MessageList.tsx`:**

   * Accepts `messages: ChatMessage[]`.
   * Wraps the list with `ScrollArea`.
   * Uses `map` to render `MessageItem`s.
   * Adds **auto-scroll** to the latest message (using `useRef` + `useEffect`).
3. **`MessageInput.tsx`:**

   * Contains an `Input` for typing and a `Button` to send.
   * Props: `onSendMessage` (function), `isLoading` (boolean).
   * Disables `Button` when `isLoading` is `true`.
4. **Supporting Components:**

   * Configure `AlertDialog` for confirming chat deletion.
   * Configure `Alert` to show error messages.

---

#### **Phase 4: Full Assembly**

*Goal: Connect logic and UI into a complete application.*

1. **`ChatView.tsx`:**

   * The main parent component that contains the entire chat interface.
   * Calls `useChat()` to access state (`messages`, `isLoading`, `error`) and methods (`sendMessage`, `clearChat`).
2. **Bind Data to UI:**

   * Pass `messages` to `MessageList`.
   * Pass `sendMessage` and `isLoading` to `MessageInput`.
   * Pass `clearChat` to the button that triggers `AlertDialog`.
3. **Conditional Rendering:**

   * Show error `Alert` if `error` exists.
   * Show `AlertDialog` when the user clicks delete.
4. **Finish:**

   * Render `ChatView` in `App.tsx`.
   * Run the app and verify the overall workflow.

