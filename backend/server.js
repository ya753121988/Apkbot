const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const User = require('./models/User');
const AppRequest = require('./models/AppRequest');

const app = express();
app.use(express.json());
app.use(cors());

mongoose.connect('mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
.then(() => console.log("DB Connected"));

// Auth
app.post('/api/signup', async (req, res) => {
    try {
        const user = new User(req.body);
        await user.save();
        res.json({ success: true });
    } catch (e) { res.status(400).json({ error: e.message }); }
});

app.post('/api/login', async (req, res) => {
    const user = await User.findOne({ email: req.body.email, password: req.body.password });
    if (user) res.json(user);
    else res.status(400).json({ error: "Invalid login" });
});

// Admin Panel API
app.post('/api/admin/add-balance', async (req, res) => {
    const { email, amount, adminPass } = req.body;
    if(adminPass !== "admin789") return res.status(403).send("Unauthorized");
    const user = await User.findOneAndUpdate({ email }, { $inc: { balance: amount } });
    res.json({ success: true, newBalance: user.balance + amount });
});

app.get('/api/admin/users', async (req, res) => {
    const users = await User.find({});
    res.json(users);
});

// App Order Logic
app.post('/api/build-app', async (req, res) => {
    const { userId, appName, url, color, platform } = req.body;
    const user = await User.findById(userId);
    const cost = 500;

    if (user.balance < cost) return res.status(400).json({ error: "Insufficient Balance" });

    user.balance -= cost;
    await user.save();

    const newRequest = new AppRequest({ userId, appName, url, color, platform });
    await newRequest.save();

    res.json({ success: true, message: "Build process started!" });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server on ${PORT}`));
