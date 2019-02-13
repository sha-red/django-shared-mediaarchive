django.jQuery(function($) {
	if (!document.body.classList.contains('change-list'))
		return;

	var dragCounter = 0,
		results = $('.results');

	results.on('drag dragstart dragend dragover dragenter dragleave drop', function(e) {
		e.preventDefault();
		e.stopPropagation();
		console.log(e);
	}).on('dragover dragenter', function(e) {
		++dragCounter;
		results.addClass('dragover');
	}).on('dragleave dragend', function(e) {
		if (--dragCounter <= 0)
			results.removeClass('dragover');
	}).on('mouseleave mouseout drop', function(e) {
		dragCounter = 0;
		results.removeClass('dragover');
	}).on('drop', function(e) {
		dragCounter = 0;
		results.removeClass('dragover');

		var files = e.originalEvent.dataTransfer.files,
			success = 0,
			progress = $('<div class="progress">0 / ' + files.length + '</div>');

		progress.appendTo(results);

		for (var i=0; i<files.length; ++i) {
			var d = new FormData();
			d.append('csrfmiddlewaretoken', $('input[name=csrfmiddlewaretoken]').val());
			d.append('file', files[i]);

			$.ajax({
				url: './upload/' + window.location.search,
				type: 'POST',
				data: d,
				contentType: false,
				processData: false,
				success: function() {
					progress.html('' + ++success + ' / ' + files.length);
					if (success >= files.length) {
						window.location.reload();
					}
				},
				xhr: function() {
					var xhr = new XMLHttpRequest();
					xhr.upload.addEventListener('progress', function(e) {
						if (e.lengthComputable) {
							progress.html(
								Math.round(e.loaded / e.total * 100) + '% of ' +
								(success + 1) + ' / ' + files.length
							);
						}
					}, false);
					return xhr;
				},
			});
		}
	});
});
