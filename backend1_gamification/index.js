const express = require("express");
const cron = require("node-cron");

const app = express();
app.use(express.json());

let users = [
  { id: 1, total_xp: 0, streak_count: 0, last_learn_date: null }
];

let posts = [];

// Gamification API
app.post("/learn/:userId", (req, res) => {
  const user = users.find(u => u.id == req.params.userId);
  const today = new Date().toISOString().slice(0, 10);

  if (user.last_learn_date !== today) {
    user.streak_count++;
    user.last_learn_date = today;
  }
  user.total_xp += 10;
  res.json(user);
});

// Social APIs
app.post("/posts", (req, res) => {
  posts.push({ id: posts.length + 1, content: req.body.content, likes: 0, comments: [] });
  res.json(posts);
});

app.post("/posts/:id/like", (req, res) => {
  const post = posts.find(p => p.id == req.params.id);
  post.likes++;
  res.json(post);
});

app.post("/posts/:id/comment", (req, res) => {
  const post = posts.find(p => p.id == req.params.id);
  post.comments.push(req.body.comment);
  res.json(post);
});

// Background job
cron.schedule("0 0 * * *", () => {
  users.forEach(u => u.streak_count = 0);
});

app.listen(3000, () => console.log("Backend1 running"));
