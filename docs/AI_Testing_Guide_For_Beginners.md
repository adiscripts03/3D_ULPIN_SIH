# 🚀 The Ultimate Beginner's Guide to Testing the 3D ULPIN AI Magic! 🪄

Welcome! This guide is written so simply that even a 5-year-old could follow it. We are going to test how smart our computer (AI) is at turning pictures and words into a full 3D building!

Follow these steps exactly, and let's make some magic happen.

---

## Step 1: Waking Up the Robot 🤖 (Starting the App)

Before we can play, we need to turn the AI on.

1. Open your computer's terminal (or command prompt).
2. Make sure you are inside the project folder: `c:\Users\bisha\Desktop\ULPIN_NEW\3D_UPLIN_SIH`.
3. Type this magic spell and press **Enter**:
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Wait until you see a message that says "Application startup complete". This means the robot is awake!

---

## Step 2: Going to the Magic Page 🌐

1. Open your favorite web browser (like Chrome or Edge).
2. In the top bar where you type website names, type exactly this and press Enter:
   **`http://localhost:8000/ai-pipeline`**
3. Wow! You should now see a cool, dark page titled **"Generate Any College Building From Images, in 3D"**. 

Now, let's play with the 5 different AI powers!

---

## Step 3: Test Power #1 🗣️ "The Reader" (Text AI)

Let's see if the AI can build a 3D building just by reading a sentence!

1. Look for the box that says **"Building Description (Optional)"**.
2. Type a story in it, like this:
   *“A 5-floor college hostel with 10 rooms per floor. It has 4-seater rooms and washrooms.”*
3. Make sure the switches for **"Use YOLOv8"** and **"Save to DB"** are turned **ON** (blue).
4. Click the big, shiny purple button at the bottom: **🚀 Generate 3D Building**.
5. **Watch the magic!** On the right side, you will see a green **"✓ Success"** badge and a colorful spinning 3D model of your building! (It might take a few seconds).

---

## Step 4: Test Power #2 🗺️ "The Map Reader" (Floor Plan AI)

Now let's see if it can read a drawing of a building!

1. Reload the page by pressing **F5** to start fresh.
2. Find the box on the left that has a map icon 🗺️ and says **"Drop floor plan here"**.
3. Click on it. A window will pop up. Choose any picture of a floor plan you have (it can be a PNG, JPG, or PDF).
4. Click the big purple **🚀 Generate 3D Building** button again.
5. The AI is now looking closely at your drawing, finding every single wall, and building a 3D model out of it! Check the right side for the results.

---

## Step 5: Test Power #3 🏢 "The Floor Counter" (Exterior AI)

Can the AI count floors just by looking at the outside of a building? Let's find out!

1. Reload the page (press **F5**).
2. Find the box with the building icon 🏢 that says **"Drop exterior photo here"**.
3. Click it and pick a picture of a tall building from the outside.
4. Click the purple **🚀 Generate 3D Building** button.
5. Look at the results log on the right side. You will see a message saying "Exterior Floor Count · X floors detected"! The AI counted the floors for you!

---

## Step 6: Test Power #4 🛏️ "The Room Detective" (Interior AI)

Let's show the AI pictures of inside rooms and see if it knows what they are!

1. Reload the page.
2. Find the three small boxes that say **Room 1, Room 2, and Room 3**.
3. Click **Room 1** and upload a picture of a bedroom or hostel room.
4. Click **Room 2** and upload a picture of a bathroom.
5. Click the purple **🚀 Generate 3D Building** button.
6. Check the stages on the right side. It will say "Room Type Classification" and it will use those pictures to decide what kind of building it is!

---

## Step 7: Test Power #5 💥 "The Ultimate Combo" (Fusion AI)

This is the ultimate test. We will use ALL powers at the same time!

1. Reload the page one last time.
2. Type a story in the **Text** box.
3. Upload a drawing to the **Floor Plan** box.
4. Upload an outside building picture to the **Exterior Photo** box.
5. Upload some room pictures to the **Room** boxes.
6. Give your building a name in the **Building ID** box, like `MY_SUPER_BUILDING`.
7. Click the purple **🚀 Generate 3D Building** button!

The AI will mix all the clues together like a detective. The drawing gives the shape, the outside picture gives the height, and the story fills in the blanks!

### 🎉 What to look for at the end:
*   **The 3D Picture**: You should see a cool 3D blocky model that you can spin around with your mouse.
*   **Total Parcels**: It will tell you exactly how many 3D rooms it created.
*   **Topology Passed**: Look for the Green Checkmark ✅ that says "Topology Passed". That means no rooms are crashing into each other. Perfect geometry!

You are now a certified AI tester! Have fun! 🎈
