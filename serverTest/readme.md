# Point Cloud Viewer Server

## Description
This is a server and viewer for rendering point clouds, built using **C**, **Three.js**, and **PLY** file format. The server serves `.ply` files for visualization and allows you to interact with point clouds in the browser.

---

## Requirements

- **C compiler** (e.g., `gcc`)
- **Three.js** (for the viewer side)
- A set of **PLY files** to visualize

---

## Setup and Compilation

### 1. **Download PLY Files**
First, download the PLY files you want to visualize.

You can download the necessary PLY files from the following link:
[PLY Files](https://drive.google.com/file/d/1QtdAbj_vO9G5VM8RE3H2z5SxbrlDmaeD/view?usp=share_link)

### 2. **Server Setup**

- Clone or download the source code to your machine.
- Navigate to the directory containing the server code (`server.c`).
  
#### Compile the Server Code:
```bash
gcc server.c -o server
````

#### Start the Server:

The server needs a directory containing the PLY files as an argument. Use the following command to start the server, replacing `/yourDirectory/plyAll` with the path to your local directory that contains the PLY files:

```bash
./server /yourDirectory/plyAll
```

The server will start and listen for incoming connections on port `9090`.

---

## Running the Viewer

### 1. **Open the Viewer**

Once the server is running, open your browser and navigate to:

```
http://localhost:9090/viewer.html
```

This will load the viewer interface where you can interact with the point clouds.

---

## Features

* **Category Selection**: Choose the category of point cloud you want to view.
* **Codec Selection**: Choose the codec (e.g., JPEG, AVC, Original) for the point cloud data.
* **QP Selection**: Choose the quality setting for the point cloud data.
* **Frame Selection**: Choose the specific frame to visualize.
* **Point Size Control**: Adjust the size of the points for better visualization.
* **Navigation Controls**: Use buttons to switch between predefined viewpoints (e.g., Top, Bottom, Front, Back, Left, Right).

---

## Troubleshooting

* **Error: Unable to find the PLY file**

  * Ensure that the `BASE_DIR` in the server is correctly set to the path containing your PLY files.

* **Error: Can't connect to localhost:9090**

  * Ensure that the server is running and that port `9090` is not blocked by a firewall.

* **Error: Server crashes or cannot start**

  * Ensure you have compiled the server properly using `gcc`.
  * Verify that the PLY file directory path is correctly provided when starting the server.

---

## License

This project is open source and available under the MIT License. Feel free to modify and distribute it as needed!

---

## Notes

* Ensure your server directory is correctly pointing to the location of the **PLY files**.
* The server supports **JPEG**, **AVC**, and **Original** codec formats for the point cloud data.
* The viewer allows you to control the visualization of the point cloud with adjustable point sizes and frame selection.

For further details or contributions, feel free to contact the project maintainers.
