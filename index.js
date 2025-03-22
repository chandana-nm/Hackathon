import express from "express";
import axios from "axios";
import bodyParser from "body-parser";

const app = express();
const port = 3000;
const API_URL = "http://localhost:4000";
const PYTHON_API_URL = "http://localhost:8000"; // FastAPI backend for sign language recognition

app.use(express.static('public'));

// Increase the body size limit for JSON and URL-encoded data
app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '50mb' }));

app.get("/", (req, res) => {
    res.render('home.ejs');
});

app.get("/tutorials", (req, res) => {
    res.render("tutorials.ejs");
});

app.get("/login", (req, res) => {
    res.render("login.ejs");
});

// New route for quizzes
app.get("/quiz", (req, res) => {
    res.render("quiz.ejs");
});

app.get("/about-us",(req,res)=>{
    res.render("about-us.ejs");
});
// API endpoint to proxy requests to the Python backend
app.post("/api/quiz", async (req, res) => {
    try {
        // Forward the request to the Python backend
        const response = await axios.post(`${PYTHON_API_URL}/api/quiz`, req.body, {
            headers: {
                'Content-Type': 'application/json'
            },
            maxContentLength: Infinity,
            maxBodyLength: Infinity
        });
        
        // Return the Python backend's response
        res.json(response.data);
    } catch (error) {
        console.error("Error forwarding to Python backend:", error.message);
        res.status(500).json({
            error: "Failed to process sign language recognition",
            details: error.message
        });
    }
});

// Existing routes for tutorials
app.get("/tutorials/basics", async (req, res) => {
    try {
        // By default, load the Introduction video (001)
        const response = await axios.get(`${API_URL}/videolib/001`);
        res.render("basics.ejs", {
            videos: response.data
        });
    } catch (error) {
        console.error("Error fetching default video:", error.message);
        res.render("basics.ejs", {
            videos: null
        });
    }
});

app.get("/tutorials/basics/:id", async (req,res) => {
    const videoId = req.params.id;
    try {
        const response = await axios.get(`${API_URL}/videolib/${videoId}`);
        
        // Check if this is an AJAX request (looks for XHR header or accepts JSON)
        const isAjaxRequest = req.xhr || req.headers.accept.indexOf('json') > -1;
        
        if (isAjaxRequest) {
            // Return JSON for AJAX requests
            res.json({
                videos: response.data
            });
        } else {
            // Return full page for direct access
            res.render("basics.ejs", {
                videos: response.data
            });
        }
    } catch(error) {
        console.error("Error fetching video:", error.message);
        if (req.xhr || req.headers.accept.indexOf('json') > -1) {
            res.status(500).json({message: "Error fetching the video"});
        } else {
            res.status(500).render("error.ejs", {message: "Error fetching the video"});
        }
    }
});

app.get("/tutorials/family-signs", async (req, res) => {
    try {
        // By default, load the Family Signs video (004)
        const response = await axios.get(`${API_URL}/videolib/004`);
        res.render("family-signs.ejs", {
            videos: response.data
        });
    } catch (error) {
        console.error("Error fetching default video:", error.message);
        res.render("family-signs.ejs", {
            videos: null
        });
    }
});

app.get("/tutorials/family-signs/:id", async (req, res) => {
    const videoId = req.params.id;
    try {
        const response = await axios.get(`${API_URL}/videolib/${videoId}`);
        
        // Check if this is an AJAX request
        const isAjaxRequest = req.xhr || req.headers.accept.indexOf('json') > -1;
        
        if (isAjaxRequest) {
            // Return JSON for AJAX requests
            res.json({
                videos: response.data
            });
        } else {
            // Return full page for direct access
            res.render("family-signs.ejs", {
                videos: response.data
            });
        }
    } catch(error) {
        console.error("Error fetching video:", error.message);
        if (req.xhr || req.headers.accept.indexOf('json') > -1) {
            res.status(500).json({message: "Error fetching the video"});
        } else {
            res.status(500).render("error.ejs", {message: "Error fetching the video"});
        }
    }
});

app.get("/tutorials/emotions-expressions", async (req, res) => {
    try {
        // By default, load the Emotions Introduction video (007)
        const response = await axios.get(`${API_URL}/videolib/005`);
        res.render("emotions-expressions.ejs", {
            videos: response.data
        });
    } catch (error) {
        console.error("Error fetching default video:", error.message);
        res.render("emotions-expressions.ejs", {
            videos: null
        });
    }
});

app.get("/tutorials/emotions-expressions/:id", async (req, res) => {
    const videoId = req.params.id;
    try {
        const response = await axios.get(`${API_URL}/videolib/${videoId}`);
        
        // Check if this is an AJAX request
        const isAjaxRequest = req.xhr || req.headers.accept.indexOf('json') > -1;
        
        if (isAjaxRequest) {
            // Return JSON for AJAX requests
            res.json({
                videos: response.data
            });
        } else {
            // Return full page for direct access
            res.render("emotions-expressions.ejs", {
                videos: response.data
            });
        }
    } catch(error) {
        console.error("Error fetching video:", error.message);
        if (req.xhr || req.headers.accept.indexOf('json') > -1) {
            res.status(500).json({message: "Error fetching the video"});
        } else {
            res.status(500).render("error.ejs", {message: "Error fetching the video"});
        }
    }
});

// Add Quiz Endpoints
app.get("/tutorials/quiz", (req, res) => {
    res.render("quiz.ejs");
});

app.get("/tutorials/quiz/:category", (req, res) => {
    const category = req.params.category;
    res.render("quiz.ejs", { category: category });
});

app.listen(port, () => {
    console.log("server listening on port " + port);
});