const express = require('express');
const mongoose = require('mongoose');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware to parse JSON requests
app.use(express.json());

// Basic Route
app.get('/', (req, res) => {
    res.send('API is running smoothly!');
});

const Item = require('./models/Item');

// 1. POST Endpoint: Insert new data
app.post('/api/items', async (req, res) => {
    try {
        const newItem = new Item({
            name: req.body.name,
            category: req.body.category,
            quantity: req.body.quantity
        });
        const savedItem = await newItem.save();
        res.status(201).json(savedItem);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 2. GET Endpoint: Fetch all data
app.get('/api/items', async (req, res) => {
    try {
        const items = await Item.find();
        res.status(200).json(items);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Start Server
app.listen(PORT, () => {
    console.log(`Server is sprinting on port ${PORT}`);
});

mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('MongoDB Connected successfully!'))
  .catch(err => console.error('Database connection error:', err));