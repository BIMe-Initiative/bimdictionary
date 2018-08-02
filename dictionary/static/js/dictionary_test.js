var rtlLanguages = ['ar', 'fa'];

var TermContent = function(data) {
    var self = this;
    self.id = ko.observable(data.id);
    self.code = ko.observable(data.code);
    self.title = ko.observable(data.title);
    self.language = ko.observable(data.language);
    self.description = ko.observable(data.description);
    self.extendedDescription = ko.observable(data.extended_description);
    self.author = ko.observable(data.author);
    self.url = ko.observable(data.url);
    self.synonyms = ko.observableArray(data.similar);
    self.acronym = ko.observable(data.acronym);
    self.version = ko.observable(data.version);
    self.permalink = ko.observable(data.permalink);
    self.oldVersion = ko.observable(false);
}

var Term = function(data) {
    var self = this;
    self.id = ko.observable(data.id);
    self._title = ko.observable(data.title);
    self.slug = ko.observable(data.slug);
    self.concepts = ko.observableArray(data.concepts);
    self.country = ko.observable(data.country);
    self.currentVersion = ko.observable(data.current_version);
    self.content = ko.observableArray();
    self.showExtended = ko.observable(false);

    $.each(data.content, function(index, value) {
        var content = new TermContent(value);
        content.oldVersion(self.currentVersion > content.version());
        self.content.push(content);
    });

    self.getCss = ko.pureComputed(function() {
        var bits = [];
        if(self.isRtl()) {
            bits.push('rtl');
        }
        return bits.join(' ');
    });

    self.currentLanguage = ko.observable('en');

    self.currentLanguage.subscribe(function(val) {
        sessionStorage[self.id()] = val;
    });

    self.currentContent = ko.pureComputed(function() {
        var current = null;
        $.each(self.content(), function(index, value) {
            if(value.language() === self.currentLanguage()){
                current = value;
            }
        })
        return current;
    });

    self.title = ko.pureComputed(function() {
        return self.currentContent().title() || self._title();
    });

    self.version = ko.pureComputed(function() {
        return self.currentContent().version();
    });

    self.code = ko.pureComputed(function() {
        return self.currentContent().code();
    });

    self.url = ko.pureComputed(function() {
        return self.currentContent().url();
    });

    self.description = ko.pureComputed(function() {
        return self.currentContent().description();
    });

    self.extendedDescription = ko.pureComputed(function() {
        return self.currentContent().extendedDescription();
    });

    self.author = ko.pureComputed(function() {
        return self.currentContent().author();
    });

    self.acronym = ko.pureComputed(function() {
        return self.currentContent().acronym();
    });

    self.isRtl = ko.pureComputed(function() {
        if(self.currentContent()) {
            return rtlLanguages.indexOf(self.currentContent().language()) >= 0;
        } else {
            return false;
        }
    });

    self.synonyms = ko.pureComputed(function() {
        return self.currentContent().synonyms();
    });

    self.permalink = ko.pureComputed(function() {
        return self.currentContent().permalink();
    });

    self.languages = ko.pureComputed(function() {
        var languages = $.map(self.content(), function(val, i) {
            return val.language();
        })
        languages.sort();
        return languages;
    });

    self.flagUrl = ko.computed(function() {
        if(data.country != undefined) {
            return 'https://bimdictionary.s3.amazonaws.com/flags/' + data.country.toLowerCase() + '.gif';
        }
    });

    self.toggleExtended = function() {
        self.showExtended(!self.showExtended());
    }

}

var TermManager = function() {
    var self = this;
    self.terms = ko.observableArray();
    self.filter = ko.observable();
    self.totalCount = ko.observable();
    self.page = ko.observable(1);
    self.loading = ko.observable(false);
    self.languages = ko.observableArray(languages);
    self.filterCountry = ko.observable();
    self.countries = ko.observable(countries);
    self.concepts = ko.observableArray();
    self.filterConcept = ko.observable();
    self.filterLanguage = ko.observable();
    self.filter.subscribe(function() {
        self.search(true);
    });
    self.filterCountry.subscribe(function() {
        self.search(true);
    });
    self.filterConcept.subscribe(function(val) {
        self.search(true);
    });
    self.filterLanguage.subscribe(function(val) {
        self.search(true);
    });
    self.isFiltered = ko.pureComputed(function() {
        return self.filterCountry() ||
            self.filterLanguage() ||
            self.filterConcept() ||
            self.filter();
    });
    self.filterLanguageIsRtl = ko.pureComputed(function() {
        return self.filterLanguage() && rtlLanguages.indexOf(self.filterLanguage().code) >= 0;
    });
    self.hasMore = ko.computed(function() {
        return self.terms().length < self.totalCount();
    });
    self.filter.extend({rateLimit: 500});
    self.load = function() {
        ko.applyBindings(self);
        self.search();
        self.concepts([]);
        $.get('/api/v1/dictionary/concepts/').done(function(data) {
            $.each(data, function(index, value) {
                self.concepts.push(value.title);
            });
        });
    }

    self.clearFilters = function() {
        self.filter(null);
        self.filterCountry(null);
        self.filterConcept(null);
        self.filterLanguage(null);
        self.search(true);
    }

    self.showMore = function() {
        //TODO handle paging properly
        self.page(self.page() + 1);
        self.search(false);
    }

    self.termCache = {}

    //self.makePopover = function(term, data) {
    //    if(data.results.length) {
    //        term.data('content', data.results[0].description);
    //        term.popover({
    //            html: true,
    //            trigger: 'focus',
    //        });
    //    } else {
    //        term.replaceWith(term.text());
    //    }
    //}

    self.search = function(clearResults) {
        self.loading(true);
        if(clearResults) {
            self.page(1);
        }
        var args = {
            page: self.page()
        }
        if(self.filter()) {
            args.q = self.filter();
        }
        if(self.filterCountry()) {
            args.country = self.filterCountry().code;
        }
        if(self.filterLanguage()) {
            args.language = self.filterLanguage().code;
        }
        if(self.filterConcept()) {
            args.concept = self.filterConcept();
        }

        $.get('/api/v1/dictionary/', args).done(function(data) {
            if(clearResults) {
                self.terms([]);
            }
            self.totalCount(data.count);
            $.each(data.results, function(index, value) {
                var term = new Term(value);
                sessionStorage.setItem(term.id(), 'en');

                // Display translation if filterLanguage is selected
                if(self.filterLanguage()) {
                    $.each(term.languages(), function(index, value) {
                        if(value == self.filterLanguage().code) {
                            term.currentLanguage(value);
                        }
                    });
                }
                self.terms.push(term);
            });

            self.loading(false);

            if(self.filter() && self.filter().length >= 3) {
                ga('send', 'event', 'Terms', 'search', self.filter());
            }
        });
    }
}

var manager = new TermManager();
manager.load();


