const express = require("express");
const axios = require("axios");

const app = express();
const PORT = 3000;

app.get("/", (req, res) => {
  res.send("Hello, Express!");
});

// FastAPI 호출
app.get("/find-path", async (req, res) => {
  try {
    const response = await axios.get("http://127.0.0.1:8000/path");
    res.json(response.data);
  } catch (error) {
    res.status(500).send("FastAPI 서버 오류");
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Express 서버 실행 중: http://localhost:${PORT}`);
});