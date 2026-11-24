// agent-kb OpenCode V2 server plugin.
//
// OpenCode V2 has no stdin/stdout hook protocol. This plugin uses the
// session prompt/context hooks instead, and shells out to the Python bridge
// (opencode_adapter.py) so reminder text still comes from kb_core.py.
//
// 1) First model call of a session -> inject the kb SessionStart reminder.
// 2) User prompt matching kb trigger words -> inject the capture reminder
//    on that same turn's model call.
//
// Every failure is swallowed: agent-kb must never block an OpenCode turn.
import { Plugin } from "@opencode/plugin";
import { spawn } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";

const BRIDGE =
  process.env.AGENT_KB_OPENCODE_BRIDGE ||
  join(homedir(), ".config", "opencode", "hook-bridge", "agent-kb", "opencode_adapter.py");
const PYTHON =
  process.env.AGENT_KB_PYTHON || (process.platform === "win32" ? "python" : "python3");
const BRIDGE_TIMEOUT_MS = 2500;

/** Run the Python bridge with a flat event payload and return its stdout. */
function runBridge(payload) {
  return new Promise((resolve) => {
    let child;
    try {
      child = spawn(PYTHON, [BRIDGE], {
        windowsHide: true,
        stdio: ["pipe", "pipe", "ignore"],
      });
    } catch {
      resolve("");
      return;
    }

    let output = "";
    let settled = false;
    let timer;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      if (timer) clearTimeout(timer);
      resolve(value);
    };
    timer = setTimeout(() => {
      try {
        child.kill();
      } catch {
        // ignore
      }
      finish("");
    }, BRIDGE_TIMEOUT_MS);

    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      output += chunk;
    });
    child.on("error", () => finish(""));
    child.on("close", () => finish(output));

    try {
      child.stdin.end(JSON.stringify(payload), "utf8");
    } catch {
      finish("");
    }
  });
}

/** Pull additionalContext out of the bridge JSON, silently on any bad shape. */
function contextOf(stdout) {
  if (!stdout || !stdout.trim()) return "";
  try {
    const parsed = JSON.parse(stdout);
    const context = parsed?.hookSpecificOutput?.additionalContext;
    return typeof context === "string" ? context : "";
  } catch {
    return "";
  }
}

export default Plugin.define({
  id: "agent-kb",
  async setup(ctx) {
    let startText = "";
    let captureText = "";
    try {
      startText = contextOf(await runBridge({ hook_event_name: "SessionStart" }));
      captureText = contextOf(
        await runBridge({ hook_event_name: "UserPromptSubmit", prompt: "记住" }),
      );
    } catch {
      // A missing bridge or Python must degrade to a no-op plugin.
    }

    // Sessions whose start reminder was already injected in this process.
    const started = new Set();
    // sessionID -> capture reminder waiting for the next model call.
    const pending = new Map();
    const registrations = [];

    registrations.push(
      await ctx.session.hook("prompt", async (event) => {
        try {
          const text = event?.prompt?.text;
          if (!text || !captureText) return;
          const context = contextOf(
            await runBridge({ hook_event_name: "UserPromptSubmit", prompt: text }),
          );
          if (context) pending.set(event.sessionID, context);
        } catch {
          // Never block prompt admission.
        }
      }),
    );

    registrations.push(
      await ctx.session.hook("context", (event) => {
        try {
          const sessionID = event?.sessionID;
          if (!sessionID) return;
          if (!started.has(sessionID) && startText) {
            started.add(sessionID);
            event.system.push({ type: "text", text: startText });
          }
          const context = pending.get(sessionID);
          if (context) {
            pending.delete(sessionID);
            event.system.push({ type: "text", text: context });
          }
        } catch {
          // Never block model dispatch.
        }
      }),
    );

    // Drop per-session state when OpenCode removes a session.
    const controller = new AbortController();
    void (async () => {
      try {
        for await (const event of ctx.event.subscribe({
          types: ["session.deleted"],
          signal: controller.signal,
        })) {
          const sessionID =
            event?.sessionID || event?.properties?.sessionID || event?.properties?.info?.id;
          if (sessionID) {
            started.delete(sessionID);
            pending.delete(sessionID);
          }
        }
      } catch {
        // Event subscription is best-effort; hooks still work without it.
      }
    })();

    return async () => {
      controller.abort();
      for (const registration of registrations) {
        try {
          await registration.dispose();
        } catch {
          // Best-effort cleanup; OpenCode unloads the plugin anyway.
        }
      }
    };
  },
});
