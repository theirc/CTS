module.exports = function(grunt) {
    // load all grunt tasks
    require('matchdep').filterDev('grunt-*').forEach(grunt.loadNpmTasks);

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        sass: {
            dist: {
                options: {
                    style: 'compressed',
                    loadPath: ['cts/static/sass/vendor/stylesheets', 'cts/static/sass/partials']
                },
                files: {
                    'cts/static/css/site.css': 'cts/static/sass/site.scss'
                }
            },
            dev: {
                options: {
                    sourcemap: true,
                    style: 'expanded',
                    loadPath: ['cts/static/sass/vendor/stylesheets', 'cts/static/sass/partials']
                },
                files: {
                    'cts/static/css/site.css': 'cts/static/sass/site.scss'
                }
            }
        },

        watch: {
            sass: {
                files: ['cts/static/sass/{,**}/*.scss'],
                tasks: ['sass:dev']
            }
        }
    });

    // Default task(s).
    grunt.registerTask('default', ['sass:dist']);

};
