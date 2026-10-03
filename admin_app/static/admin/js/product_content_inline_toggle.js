/**
 * Show/hide Lesson vs Assessment inline based on ProductContent.content_type.
 * Only applies on ProductContent add/change pages.
 */
(function() {
    'use strict';

    function toggleInlines() {
        var contentTypeSelect = document.getElementById('id_content_type');
        if (!contentTypeSelect) return;

        var contentType = contentTypeSelect.value;
        var lessonGroup = document.querySelector('.inline-group[id$="-group"]');
        var allInlineGroups = document.querySelectorAll('.inline-group[id$="-group"]');

        // Find Lesson and Assessment inline groups by their heading text
        var lessonGroupEl = null;
        var assessmentGroupEl = null;
        allInlineGroups.forEach(function(grp) {
            var h2 = grp.querySelector('h2');
            if (h2) {
                var text = h2.textContent || '';
                if (text.indexOf('Lesson content') !== -1) lessonGroupEl = grp;
                if (text.indexOf('Assessment content') !== -1) assessmentGroupEl = grp;
            }
        });

        function show(el) {
            if (el) el.style.display = '';
        }
        function hide(el) {
            if (el) el.style.display = 'none';
        }

        if (contentType === 'LESSON') {
            show(lessonGroupEl);
            hide(assessmentGroupEl);
        } else if (contentType === 'ASSESSMENT') {
            hide(lessonGroupEl);
            show(assessmentGroupEl);
        } else {
            show(lessonGroupEl);
            show(assessmentGroupEl);
        }
    }

    function init() {
        toggleInlines();
        var contentTypeSelect = document.getElementById('id_content_type');
        if (contentTypeSelect) {
            contentTypeSelect.addEventListener('change', toggleInlines);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
