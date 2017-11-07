#include <iostream>
#include <fstream>
#include <cmath>
#include <opencv2/opencv.hpp>

#include <json/json.h>
#include "MatterSim.hpp"
#include "Benchmark.hpp"

namespace mattersim {

// cube indices for index buffer object
GLushort cube_indices[] = {
    0, 1, 2, 3,
    3, 2, 6, 7,
    7, 6, 5, 4,
    4, 5, 1, 0,
    0, 3, 7, 4,
    1, 2, 6, 5,
};

char* loadFile(const char *filename) {
    char* data;
    int len;
    std::ifstream ifs(filename, std::ifstream::in);

    ifs.seekg(0, std::ios::end);
    len = ifs.tellg();

    ifs.seekg(0, std::ios::beg);
    data = new char[len + 1];

    ifs.read(data, len);
    data[len] = 0;

    ifs.close();

    return data;
}

void setupCubeMap(GLuint& texture) {
    glActiveTexture(GL_TEXTURE0);
    glEnable(GL_TEXTURE_CUBE_MAP);
    glGenTextures(1, &texture);
    glBindTexture(GL_TEXTURE_CUBE_MAP, texture);
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE);
}

void setupCubeMap(GLuint& texture, cv::Mat &xpos, cv::Mat &xneg, cv::Mat &ypos, cv::Mat &yneg, cv::Mat &zpos, cv::Mat &zneg) {
    setupCubeMap(texture);
    //use fast 4-byte alignment (default anyway) if possible
    glPixelStorei(GL_UNPACK_ALIGNMENT, (xneg.step & 3) ? 1 : 4);
    //set length of one complete row in data (doesn't need to equal image.cols)
    glPixelStorei(GL_UNPACK_ROW_LENGTH, xneg.step/xneg.elemSize());
    glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X, 0, GL_RGB, xpos.rows, xpos.cols, 0, GL_BGR, GL_UNSIGNED_BYTE, xpos.ptr());
    glTexImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_X, 0, GL_RGB, xneg.rows, xneg.cols, 0, GL_BGR, GL_UNSIGNED_BYTE, xneg.ptr());
    glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_Y, 0, GL_RGB, ypos.rows, ypos.cols, 0, GL_BGR, GL_UNSIGNED_BYTE, ypos.ptr());
    glTexImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_Y, 0, GL_RGB, yneg.rows, yneg.cols, 0, GL_BGR, GL_UNSIGNED_BYTE, yneg.ptr());
    glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_Z, 0, GL_RGB, zpos.rows, zpos.cols, 0, GL_BGR, GL_UNSIGNED_BYTE, zpos.ptr());
    glTexImage2D(GL_TEXTURE_CUBE_MAP_NEGATIVE_Z, 0, GL_RGB, zneg.rows, zneg.cols, 0, GL_BGR, GL_UNSIGNED_BYTE, zneg.ptr());
}

Simulator::Simulator() :state{new SimState()},
                        width(320),
                        height(240),
                        vfov(45.0),
                        minElevation(-0.94),
                        maxElevation(0.94),
                        navGraphPath("./connectivity"),
                        datasetPath("./data"),
#ifdef OSMESA_RENDERING
                        buffer(NULL),
#endif
                        initialized(false),
                        renderingEnabled(true) {
    generator.seed(time(NULL));
};

Simulator::~Simulator() {
    close();
}


void Simulator::setCameraResolution(int width, int height) {
    this->width = width;
    this->height = height;
}

void Simulator::setCameraFOV(double vfov) {
    this->vfov = vfov;
}

void Simulator::setRenderingEnabled(bool value) {
    if (!initialized) {
        renderingEnabled = value;
    }
}


void Simulator::setDatasetPath(const std::string& path) {
    datasetPath = path;
}

void Simulator::setNavGraphPath(const std::string& path) {
    navGraphPath = path;
}

void Simulator::init() {
    state->rgb.create(height, width, CV_8UC3);
    if (renderingEnabled) {
#ifdef OSMESA_RENDERING
        ctx = OSMesaCreateContext(OSMESA_RGBA, NULL);
        buffer = malloc(width * height * 4 * sizeof(GLubyte));
        if (!buffer) {
            throw std::runtime_error( "Malloc image buffer failed" );
        }
        if (!OSMesaMakeCurrent(ctx, buffer, GL_UNSIGNED_BYTE, width, height)) {
            throw std::runtime_error( "OSMesaMakeCurrent failed" );
        }
#else
        cv::namedWindow("renderwin", cv::WINDOW_OPENGL);
        cv::setOpenGlContext("renderwin");
        // initialize the extension wrangler
        glewInit();
#endif

#ifndef OSMESA_RENDERING
        FramebufferName = 0;
        glGenFramebuffers(1, &FramebufferName);
        glBindFramebuffer(GL_FRAMEBUFFER, FramebufferName);

        // The texture we're going to render to
        GLuint renderedTexture;
        glGenTextures(1, &renderedTexture);

        // "Bind" the newly created texture : all future texture functions will modify this texture
        glBindTexture(GL_TEXTURE_2D, renderedTexture);

        // Give an empty image to OpenGL ( the last "0" )
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0,GL_RGB, GL_UNSIGNED_BYTE, 0);

        // Poor filtering. Needed !
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);

        // Set "renderedTexture" as our colour attachement #0
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, renderedTexture, 0);

        // Set the list of draw buffers.
        GLenum DrawBuffers[1] = {GL_COLOR_ATTACHMENT0};
        glDrawBuffers(1, DrawBuffers); // "1" is the size of DrawBuffers

        // Always check that our framebuffer is ok
        if(glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) {
            throw std::runtime_error( "GL_FRAMEBUFFER failure" );
        }
#endif

        // set our viewport, clear color and depth, and enable depth testing
        glViewport(0, 0, this->width, this->height);
        glClearColor(1.0f, 0.0f, 0.0f, 1.0f);
        glClearDepth(1.0f);
        glEnable(GL_DEPTH_TEST);
        glDepthFunc(GL_LEQUAL);

        // load our shaders and compile them.. create a program and link it
        glShaderV = glCreateShader(GL_VERTEX_SHADER);
        glShaderF = glCreateShader(GL_FRAGMENT_SHADER);
        const GLchar* vShaderSource = loadFile("src/lib/vertex.sh");
        const GLchar* fShaderSource = loadFile("src/lib/fragment.sh");
        glShaderSource(glShaderV, 1, &vShaderSource, NULL);
        glShaderSource(glShaderF, 1, &fShaderSource, NULL);
        delete [] vShaderSource;
        delete [] fShaderSource;
        glCompileShader(glShaderV);
        glCompileShader(glShaderF);
        glProgram = glCreateProgram();
        glAttachShader(glProgram, glShaderV);
        glAttachShader(glProgram, glShaderF);
        glLinkProgram(glProgram);
        glUseProgram(glProgram);

        // shader logs
        int  vlength,    flength;
        char vlog[2048], flog[2048];
        glGetShaderInfoLog(glShaderV, 2048, &vlength, vlog);
        glGetShaderInfoLog(glShaderF, 2048, &flength, flog);

        // grab the pvm matrix and vertex location from our shader program
        PVM    = glGetUniformLocation(glProgram, "PVM");
        vertex = glGetAttribLocation(glProgram, "vertex");

        // these won't change
        Projection = glm::perspective((float)vfov, (float)width / (float)height, 0.1f, 100.0f);
        Scale      = glm::scale(glm::mat4(1.0f),glm::vec3(10,10,10)); // Scale cube to 10m

        // cube vertices for vertex buffer object
        GLfloat cube_vertices[] = {
          -1.0,  1.0,  1.0,
          -1.0, -1.0,  1.0,
            1.0, -1.0,  1.0,
            1.0,  1.0,  1.0,
          -1.0,  1.0, -1.0,
          -1.0, -1.0, -1.0,
            1.0, -1.0, -1.0,
            1.0,  1.0, -1.0,
        };
        glGenBuffers(1, &vbo_cube_vertices);
        glBindBuffer(GL_ARRAY_BUFFER, vbo_cube_vertices);
        glBufferData(GL_ARRAY_BUFFER, sizeof(cube_vertices), cube_vertices, GL_STATIC_DRAW);
        glEnableVertexAttribArray(vertex);
        glVertexAttribPointer(vertex, 3, GL_FLOAT, GL_FALSE, 0, 0);

        glGenBuffers(1, &ibo_cube_indices);
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo_cube_indices);
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(cube_indices), cube_indices, GL_STATIC_DRAW);
    } else {
        // no rendering, e.g. for unit testing
        state->rgb.setTo(cv::Scalar(0, 0, 0)); 
    }
    initialized = true;
}

void Simulator::clearLocationGraph() {
    for (auto loc : locations) {
       glDeleteTextures(1, &loc->cubemap_texture);
    }
    locations.clear();
}

void Simulator::loadLocationGraph() {
    Json::Value root;
    auto navGraphFile =  navGraphPath + "/" + state->scanId + "_connectivity.json";
    std::ifstream ifs(navGraphFile, std::ifstream::in);
    if (ifs.fail()){
        throw std::invalid_argument( "Could not open navigation graph file: " +
                navGraphFile + ", is scan id valid?" );
    }
    ifs >> root;
    for (auto viewpoint : root) {
        float posearr[16];
        int i = 0;
        for (auto f : viewpoint["pose"]) {
            posearr[i++] = f.asFloat();
        }
        // glm uses column-major order. Inputs are in row-major order. 
        glm::mat4 mattPose = glm::transpose(glm::make_mat4(posearr));
        // glm access is col,row
        glm::vec3 pos{mattPose[3][0], mattPose[3][1], mattPose[3][2]};
        mattPose[3] = {0,0,0,1}; // remove translation component
        // Matterport camera looks down z axis. Opengl camera looks down -z axis. Rotate around x by 180 deg.
        glm::mat4 openglPose = glm::rotate(mattPose, (float)M_PI, glm::vec3(1.0f, 0.0f, 0.0f));
        std::vector<bool> unobstructed;
        for (auto u : viewpoint["unobstructed"]) {
            unobstructed.push_back(u.asBool());
        }
        auto viewpointId = viewpoint["image_id"].asString();
        GLuint cubemap_texture = 0;
        Location l{viewpoint["included"].asBool(), viewpointId, openglPose, pos, unobstructed, cubemap_texture};
        locations.push_back(std::make_shared<Location>(l));
    }
}

void Simulator::populateNavigable() {
    std::vector<ViewpointPtr> updatedNavigable;
    updatedNavigable.push_back(state->location);
    unsigned int idx = state->location->ix;
    unsigned int i = 0;
    cv::Point3f curPos = state->location->point;
    double adjustedheading = M_PI / 2 - state->heading;
    glm::vec3 camera_dir(cos(adjustedheading), sin(adjustedheading), 0.f);
    double cos_half_hfov = cos(vfov * width / height * M_PI / 180.f / 2.f);
    for (unsigned int i = 0; i < locations.size(); ++i) {
        if (i == idx) {
            // Current location is pushed first
            continue;
        }
        if (locations[idx]->unobstructed[i] && locations[i]->included) {
            // Check if visible between camera left and camera right
            glm::vec3 target_dir = locations[i]->pos - locations[idx]->pos;
            target_dir.z = 0.f; // project to xy plane
            glm::vec3 normed_target_dir = glm::normalize(target_dir);
            double cos_angle = glm::dot(normed_target_dir, camera_dir);
            if (cos_angle >= cos_half_hfov) {
                glm::vec3 pos(locations[i]->pos);
                Viewpoint v{locations[i]->viewpointId, i, cv::Point3f(pos[0], pos[1], pos[2])};
                updatedNavigable.push_back(std::make_shared<Viewpoint>(v));
            }
        }
    }
    /*
    // Flush textures for locations that can no longer be reached - not sure if we should be this aggressive
    for (auto v : state->navigableLocations) {
        bool retained = false;
        for (auto updatedV : updatedNavigable) {
            if (v->ix == updatedV->ix) {
                retained = true;
                break;
            }
        }
        if (!retained) {
            glDeleteTextures(1, &locations[v->ix]->cubemap_texture);
            locations[v->ix]->cubemap_texture = 0;
        }
    }*/
    state->navigableLocations = updatedNavigable;
}

void Simulator::loadTexture(int locationId) {
    cpuLoadTimer.Start();
    if (glIsTexture(locations[locationId]->cubemap_texture)){
        // Check if it's already loaded
        return;
    }
    auto datafolder = datasetPath + "/v1/scans/" + state->scanId + "/matterport_skybox_images/";
    auto viewpointId = locations[locationId]->viewpointId;
    auto xpos = cv::imread(datafolder + viewpointId + "_skybox2_sami.jpg");
    auto xneg = cv::imread(datafolder + viewpointId + "_skybox4_sami.jpg");
    auto ypos = cv::imread(datafolder + viewpointId + "_skybox0_sami.jpg");
    auto yneg = cv::imread(datafolder + viewpointId + "_skybox5_sami.jpg");
    auto zpos = cv::imread(datafolder + viewpointId + "_skybox1_sami.jpg");
    auto zneg = cv::imread(datafolder + viewpointId + "_skybox3_sami.jpg");
    if (xpos.empty() || xneg.empty() || ypos.empty() || yneg.empty() || zpos.empty() || zneg.empty()) {
        throw std::invalid_argument( "Could not open skybox files at: " + datafolder + viewpointId + "_skybox*_sami.jpg");
    }
    cpuLoadTimer.Stop();
    gpuLoadTimer.Start();
    setupCubeMap(locations[locationId]->cubemap_texture, xpos, xneg, ypos, yneg, zpos, zneg);
    gpuLoadTimer.Stop();
    if (!glIsTexture(locations[locationId]->cubemap_texture)){
        throw std::runtime_error( "loadTexture failed" );
    }
}

void Simulator::setHeading(double heading) {
    // Normalize to range [0, 360]
    state->heading = fmod(heading, M_PI*2.f);
    while (state->heading < 0) {
        state->heading += M_PI*2.f;
    }
}

void Simulator::setElevation(double elevation) {
    state->elevation = std::max(std::min(elevation, maxElevation), minElevation);
}

bool Simulator::setElevationLimits(double min, double max) {
    if (min < 0 && min > -M_PI/2.f && max > 0 && max < M_PI/2.f) {
        minElevation = min;
        maxElevation = max;
        return true;
    } else {
        return false;
    }
}

void Simulator::newEpisode(const std::string& scanId,
                           const std::string& viewpointId,
                           double heading,
                           double elevation) {
    totalTimer.Start();
    if (!initialized) {
        init();
    }
    state->step = 0;
    setHeading(heading);
    setElevation(elevation);
    if (state->scanId != scanId) {
        // Moving to a new building...
        state->scanId = scanId;
        clearLocationGraph();
        loadLocationGraph();
    }
    int ix = -1;
    if (viewpointId.empty()) {
        // Generate a random starting viewpoint
        std::uniform_int_distribution<int> distribution(0,locations.size()-1);
        int start_ix = distribution(generator);  // generates random starting index
        ix = start_ix; 
        while (!locations[ix]->included) { // Don't start at an excluded viewpoint
            ix++;
            if (ix >= locations.size()) ix = 0;
            if (ix == start_ix) {
                throw std::logic_error( "ScanId: " + scanId + " has no included viewpoints!");
            }
        }
    } else {
        // Find index of selected viewpoint
        for (int i = 0; i < locations.size(); ++i) {
            if (locations[i]->viewpointId == viewpointId) {
                if (!locations[i]->included) {
                    throw std::invalid_argument( "ViewpointId: " +
                            viewpointId + ", is excluded from the connectivity graph." );
                }
                ix = i;
                break;
            }
        }
        if (ix < 0) {
            throw std::invalid_argument( "Could not find viewpointId: " +
                    viewpointId + ", is viewpoint id valid?" );
        }
    }
    glm::vec3 pos(locations[ix]->pos);
    Viewpoint v{locations[ix]->viewpointId, (unsigned int)ix, cv::Point3f(pos[0], pos[1], pos[2])};
    state->location = std::make_shared<Viewpoint>(v);
    populateNavigable();
    if (renderingEnabled) {
        loadTexture(state->location->ix);
        renderScene();
    }
    totalTimer.Stop();
}

SimStatePtr Simulator::getState() {
    return this->state;
}

void Simulator::renderScene() {
    renderTimer.Start();
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    // Scale and move the cubemap model into position
    Model = locations[state->location->ix]->rot * Scale;
    // Opengl camera looking down -z axis. Rotate around x by 90deg (now looking down +y). Keep rotating for - elevation.
    RotateX = glm::rotate(glm::mat4(1.0f), -(float)M_PI / 2.0f - (float)state->elevation, glm::vec3(1.0f, 0.0f, 0.0f));
    // Rotate camera for heading, positive heading will turn right.
    View = glm::rotate(RotateX, (float)state->heading, glm::vec3(0.0f, 0.0f, 1.0f));
    glm::mat4 M = Projection * View * Model;
    glUniformMatrix4fv(PVM, 1, GL_FALSE, glm::value_ptr(M));
#ifndef OSMESA_RENDERING
    // Render to our framebuffer
    glBindFramebuffer(GL_FRAMEBUFFER, FramebufferName);
#endif
    glViewport(0, 0, width, height);
    glBindTexture(GL_TEXTURE_CUBE_MAP, locations[state->location->ix]->cubemap_texture);
    glDrawElements(GL_QUADS, sizeof(cube_indices)/sizeof(GLushort), GL_UNSIGNED_SHORT, 0);
    cv::Mat img(height, width, CV_8UC3);
    //use fast 4-byte alignment (default anyway) if possible
    glPixelStorei(GL_PACK_ALIGNMENT, (img.step & 3) ? 1 : 4);
    //set length of one complete row in destination data (doesn't need to equal img.cols)
    glPixelStorei(GL_PACK_ROW_LENGTH, img.step/img.elemSize());
    glReadPixels(0, 0, img.cols, img.rows, GL_BGR, GL_UNSIGNED_BYTE, img.data);
    cv::flip(img, img, 0);
    this->state->rgb = img;
    renderTimer.Stop();
}

void Simulator::makeAction(int index, double heading, double elevation) {
    totalTimer.Start();
    // move
    if (!initialized || index < 0 || index >= state->navigableLocations.size() ){
        std::stringstream msg;
        msg << "Invalid action index: " << index;
        throw std::domain_error( msg.str() );
    }
    state->location = state->navigableLocations[index];
    state->step += 1;
    setHeading(state->heading + heading);
    setElevation(state->elevation + elevation);
    populateNavigable();
    if (renderingEnabled) {
        // loading cubemap
        if (!glIsTexture(locations[state->location->ix]->cubemap_texture)) {
            loadTexture(state->location->ix);
        }
        renderScene();
    }
    totalTimer.Stop();
    //std::cout << "\ntotalTimer: " << totalTimer.MilliSeconds() << " ms" << std::endl;
    //std::cout << "cpuLoadTimer: " << cpuLoadTimer.MilliSeconds() << " ms" << std::endl;
    //std::cout << "gpuLoadTimer: " << gpuLoadTimer.MilliSeconds() << " ms" << std::endl;
    //std::cout << "renderTimer: " << renderTimer.MilliSeconds() << " ms" << std::endl;
    //cpuLoadTimer.Reset();
    //gpuLoadTimer.Reset();
    //renderTimer.Reset();
    //totalTimer.Reset();
}

void Simulator::close() {
    if (initialized) {
        if (renderingEnabled) {
            // delete textures
            clearLocationGraph();
            // release vertex and index buffer object
            glDeleteBuffers(1, &ibo_cube_indices);
            glDeleteBuffers(1, &vbo_cube_vertices);
            // detach shaders from program and release
            glDetachShader(glProgram, glShaderF);
            glDetachShader(glProgram, glShaderV);
            glDeleteShader(glShaderF);
            glDeleteShader(glShaderV);
            glDeleteProgram(glProgram);
#ifdef OSMESA_RENDERING
            free( buffer );
            buffer = NULL;
            OSMesaDestroyContext( ctx );
#else
            cv::destroyAllWindows();
#endif
        }
        initialized = false;
    }
}
}
