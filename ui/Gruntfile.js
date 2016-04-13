/* jshint node: true */
module.exports = function(grunt) {
    'use strict';

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        // Do hinting/linting with 'grunt jshint'
        jshint: {
            files: ['Gruntfile.js', 'JGO/**/*.js', 'test/**/*.js'],
            options: {
                jshintrc: true
            }
        },

        // Use shell command until jsdoc support gets to 3.3.0 (without Java)
        shell: {
            makeDocs: {
                //command: 'echo <%= grunt.file.expand("JGO/*.js").join(" ") %>',
                command: 'jsdoc -d doc JGO', // JSDoc doesn't support expansion
                options: {
                    stdout: true,
                    stderr: true
                }
            }
        },

        browserify: {
          dist: {
            src: 'main.js',
            dest: 'dist/<%= pkg.name %>-<%= pkg.version %>.js'
          }
        },

        concat: {
            options: {
                separator: '\n',
                banner: '/*! <%= pkg.name %> <%= pkg.version %>, (c) <%= pkg.author %>. ' +
                    'Licensed under <%= pkg.license %>, see <%= pkg.homepage %> for details. */\n'
            },
            dist: {
                src: [ 'JGO/jgoinit.js', 'JGO/*.js' ],
                dest: 'dist/<%= pkg.name %>-<%= pkg.version %>.js',
            }
        },

        uglify: {
            options: {
                banner: '<%= concat.options.banner %>'
            },
            dist: {
                files: {
                    'dist/<%= pkg.name %>-<%= pkg.version %>.min.js': ['<%= concat.dist.dest %>']
                }
            }
        },

        copy: {
            main: {
                src: 'dist/<%= pkg.name %>-<%= pkg.version %>.js',
                dest: 'dist/<%= pkg.name %>-latest.js'
            }
        }
    });

    // Load the plugin that provides the "uglify" task.
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-copy');
    //grunt.loadNpmTasks('grunt-jsdoc');
    grunt.loadNpmTasks('grunt-shell');
    grunt.loadNpmTasks('grunt-browserify');

    // Default task(s).
    //grunt.registerTask('default', ['jshint', 'browserify', 'uglify', 'copy']);
    grunt.registerTask('default', ['browserify', 'copy']);
};
