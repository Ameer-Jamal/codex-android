// Real Android executable, deterministic local Responses fixture; no account/model.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");

async function main() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "codex-runtime-e2e-"));
  const home = path.join(root, "home");
  const project = path.join(root, "project");
  fs.mkdirSync(project);
  const requests = [];
  let transientInjected = false;
  const tools = [
    {
      type: "function_call",
      call_id: "shell-test",
      name: "exec_command",
      arguments: JSON.stringify({
        cmd: "printf 'android-shell-ok\\n' >> shell.txt; cat shell.txt",
      }),
    },
    {
      type: "custom_tool_call",
      call_id: "patch-test",
      name: "apply_patch",
      input:
        "*** Begin Patch\n*** Add File: edited.txt\n+android-patch-ok\n*** End Patch",
    },
    {
      type: "message",
      role: "assistant",
      id: "done",
      content: [{ type: "output_text", text: "ANDROID_E2E_COMPLETE" }],
    },
    {
      type: "message",
      role: "assistant",
      id: "resumed",
      content: [{ type: "output_text", text: "ANDROID_RESUME_COMPLETE" }],
    },
  ];
  tools.push(
    {
      type: "custom_tool_call",
      call_id: "js-test",
      name: "exec",
      input: 'text("ANDROID_JS_RUNTIME_OK");',
    },
    {
      type: "message",
      role: "assistant",
      id: "js-done",
      content: [{ type: "output_text", text: "ANDROID_JS_COMPLETE" }],
    },
  );
  const server = http.createServer(async (req, res) => {
    if (!req.url.endsWith("/responses")) {
      res.writeHead(404).end();
      return;
    }
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const body = JSON.parse(Buffer.concat(chunks).toString());
    // Drop one tool-result submission with a retryable server failure. The
    // subsequent retry must preserve the result without executing the shell twice.
    if (requests.length === 1 && !transientInjected) {
      transientInjected = true;
      res
        .writeHead(503, { "Retry-After": "0" })
        .end("temporary fixture failure");
      return;
    }
    requests.push(body);
    const item = tools[requests.length - 1];
    if (!item) {
      res.writeHead(500).end("unexpected extra request");
      return;
    }
    const id = `response-${requests.length}`;
    const events = [
      { type: "response.created", response: { id } },
      { type: "response.output_item.done", item },
      {
        type: "response.completed",
        response: {
          id,
          usage: { input_tokens: 10, output_tokens: 5, total_tokens: 15 },
        },
      },
    ];
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Connection": "close",
    });
    res.end(
      events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join(""),
    );
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const config = [
    "-c",
    'model_provider="android_fixture"',
    "-c",
    `model_providers.android_fixture={name="Android fixture",base_url="http://127.0.0.1:${server.address().port}/v1",wire_api="responses",requires_openai_auth=false,supports_websockets=false}`,
    "-c",
    "analytics.enabled=false",
  ];
  async function invoke(args, extra = []) {
    // Full access is explicit ONLY for this disposable fixture project. This does
    // not change launcher defaults or claim Android sandbox enforcement coverage.
    const child = spawn(
      "codex",
      [
        "exec",
        "--json",
        "--skip-git-repo-check",
        "-s",
        "danger-full-access",
        ...config,
        ...extra,
        ...args,
      ],
      {
        cwd: project,
        env: { ...process.env, CODEX_HOME: home, CODEX_ANDROID_USE_DAEMON: "" },
        stdio: ["ignore", "pipe", "pipe"],
      },
    );
    let out = "",
      err = "";
    child.stdout.on("data", (chunk) => {
      out += chunk;
    });
    child.stderr.on("data", (chunk) => {
      err += chunk;
    });
    const timer = setTimeout(() => child.kill("SIGKILL"), 90000);
    try {
      const code = await new Promise((resolve, reject) => {
        child.once("error", reject);
        child.once("close", resolve);
      });
      assert.equal(code, 0, err.slice(-4000));
      return out
        .trim()
        .split("\n")
        .map((line) => JSON.parse(line));
    } finally {
      clearTimeout(timer);
    }
  }
  try {
    const first = await invoke(["Android fixture first turn"]);
    if (process.env.CODEX_ANDROID_EXPECT_INSTRUCTIONS === "1") {
      assert(
        JSON.stringify(requests[0].input).includes(
          "Codex for Android environment",
        ),
        "Android global guidance missing from native model context",
      );
    }
    assert.equal(
      fs.readFileSync(path.join(project, "shell.txt"), "utf8"),
      "android-shell-ok\n",
    );
    assert.equal(
      fs.readFileSync(path.join(project, "edited.txt"), "utf8"),
      "android-patch-ok\n",
    );
    assert(first.some((event) => event.item?.text === "ANDROID_E2E_COMPLETE"));
    for (const [index, callId] of [
      [1, "shell-test"],
      [2, "patch-test"],
    ]) {
      assert(
        requests[index].input.some(
          (item) =>
            item.call_id === callId &&
            ["function_call_output", "custom_tool_call_output"].includes(
              item.type,
            ),
        ),
        `missing tool result: ${callId}`,
      );
    }
    const thread = first.find(
      (event) => event.type === "thread.started",
    )?.thread_id;
    assert(thread, "session identifier missing");
    const resumed = await invoke([
      "resume",
      thread,
      "Android fixture resume turn",
    ]);
    assert(
      resumed.some(
        (event) =>
          event.type === "thread.started" && event.thread_id === thread,
      ),
      "resume created a different session",
    );
    assert(
      resumed.some((event) => event.item?.text === "ANDROID_RESUME_COMPLETE"),
    );
    assert(
      JSON.stringify(requests[3].input).includes("ANDROID_E2E_COMPLETE"),
      "prior response missing from resumed context",
    );
    const javascript = await invoke(
      ["Android JavaScript fixture turn"],
      ["-c", "features.code_mode=true"],
    );
    assert(
      javascript.some((event) => event.item?.text === "ANDROID_JS_COMPLETE"),
    );
    const jsResult = requests[5].input.find(
      (item) =>
        item.call_id === "js-test" && item.type === "custom_tool_call_output",
    );
    assert(
      jsResult && JSON.stringify(jsResult).includes("ANDROID_JS_RUNTIME_OK"),
      "native JavaScript helper did not execute",
    );
    assert.equal(requests.length, 6);
    assert.equal(transientInjected, true);
    console.log(
      "PASS: native exec, shell, file patch, tool-result round trips, persisted session, resume, native JavaScript helper and transient network retry",
    );
  } finally {
    await new Promise((resolve) => server.close(resolve));
    fs.rmSync(root, { recursive: true, force: true });
  }
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
